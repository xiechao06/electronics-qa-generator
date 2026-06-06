"""Template-triad coverage verification.

Verifies that, for every topology, the **question template**, the **SVG
schematic template**, and the **netlist/graph** are mutually consistent —
specifically that the union of (schematic image + question text) conveys every
netlist fact a question's answer depends on.

Motivation: QA items are multimodal. A solver sees only the schematic image and
the question string; the SPICE netlist is never shown. If an answer depends on a
netlist fact (a component value, a source level, an analysis frequency) that is
visible in neither the image nor the question, the item is silently
unanswerable. This module makes that invariant checkable and deterministic — no
simulation, no LLM.

Three coverage checks per topology:

1. **netlist -> image** — every component designator and non-ground node in the
   graph must appear in the rendered schematic.
2. **netlist -> (image union question)** — for each question, every governing
   input the answer depends on must have its *value* visible in the schematic or
   be inlined in the question text.
3. Reported per-topology as PASS/FAIL with a precise locus for every failure.
"""

from __future__ import annotations

import json
import re
import string
from dataclasses import asdict, dataclass, field
from typing import Any

from ..graph.models import CircuitGraph
from ..render.svg_render import fill_template
from ..render.svg_templates import SVGTemplate, TemplateRegistry
from ..render.svg_templates import registry as default_registry

__all__ = [
    "NetlistFact",
    "CoverageFailure",
    "TopologyReport",
    "CoverageReport",
    "FACT_INPUTS",
    "netlist_facts",
    "image_present_names",
    "image_valued_designators",
    "question_referenced_nodes",
    "question_answer_inputs",
    "question_covered_designators",
    "verify_topology",
    "verify_all",
]


# ---------------------------------------------------------------------------
# Fact -> governing inputs table
# ---------------------------------------------------------------------------
#
# For each topology, map every answer-relevant fact key to the set of
# *governing inputs* a solver must read to derive it. An input is either a
# component designator (its value must be visible) or the special token
# ``"freq"`` (the analysis frequency must be shown or stated).
#
# Derived/structural facts (a passband gain that is unity by topology, a
# behaviour label that follows from the circuit shape) legitimately need no
# numeric input and map to an empty list. Device-intrinsic parameters such as a
# transistor's beta are not drawn on the schematic; questions that genuinely
# need an exact beta inline every parameter in their text, so beta is not a
# governing *visual* input here.
#
# The table is the explicit, reviewed contract. Any answer-relevant fact NOT in
# the table for its topology is reported as an ``unmapped_fact`` failure
# (fail-closed) so the table is kept complete as questions evolve.

FACT_INPUTS: dict[str, dict[str, list[str]]] = {
    "voltage_divider": {
        "Vout_dc": ["R1", "R2", "Vin"],
        "Vin_dc": ["Vin"],
    },
    "rc_lowpass": {
        "cutoff_hz": ["R1", "C1"],
        "passband_gain_db": [],
        "behavior": [],
    },
    "rc_highpass": {
        "cutoff_hz": ["R1", "C1"],
        "passband_gain_db": [],
        "behavior": [],
    },
    "rlc_bandpass": {
        "center_freq_hz": ["L1", "C1"],
        "bandwidth_hz": ["R1", "L1"],
        "behavior": [],
    },
    "half_wave_rectifier": {
        "Vout_dc": ["Vin", "D1", "Rload", "C1"],
        "Vout_peak": ["Vin", "D1"],
        "ripple_vpp": ["Vin", "Rload", "C1"],
    },
    "rc_step_response": {
        "tau_s": ["R1", "C1"],
        "v_C_initial": [],
        "v_C_final": ["Vin"],
        "v_C_at_1tau": ["Vin", "R1", "C1"],
    },
    "rl_step_response": {
        "tau_s": ["L1", "R1"],
        "i_L_final": ["Vin", "R1"],
        "i_L_initial": [],
        "i_L_at_1tau": ["Vin", "R1", "L1"],
        "R_load_ohm": ["R1"],
    },
    "ac_phasor_rc": {
        "V_C_mag_V": ["R1", "C1", "Vin", "freq"],
        "V_C_phase_deg": ["R1", "C1", "freq"],
        "Z_mag_ohm": ["R1", "C1", "freq"],
        "P_avg_mW": ["R1", "C1", "Vin", "freq"],
    },
    "bjt_ce_amplifier": {
        "V_CEQ": ["R1", "R2", "RC", "RE", "VCC"],
        "I_CQ_mA": ["R1", "R2", "RE", "VCC"],
        "A_v": ["R1", "R2", "RC", "RE", "VCC"],
        "operating_region": ["R1", "R2", "RC", "RE", "VCC"],
    },
    "bjt_emitter_follower": {
        "r_out_ohm": ["R1", "R2", "RE", "VCC"],
        "A_v": ["R1", "R2", "RE", "VCC"],
    },
    "mosfet_cs_amplifier": {
        "V_DSQ": ["RD", "RS", "RG", "VDD"],
        "I_DQ_mA": ["RD", "RS", "RG", "VDD"],
        "A_v": ["RD", "RS", "RG", "VDD"],
    },
    "resistor_network": {
        "R_eq_ohm": ["Ra", "Rb", "Rc", "Rd", "Rload"],
        "V_th_V": ["Ra", "Rb", "Rc", "Rd", "Vs"],
        "R_th_ohm": ["Ra", "Rb", "Rc", "Rd"],
        "P_source_W": ["Ra", "Rb", "Rc", "Rd", "Rload", "Vs"],
    },
    "op_amp_inverting": {
        "A_v": ["Rf", "Rin"],
        "V_out_dc": ["Rf", "Rin", "Vin"],
        "f_3dB_hz": ["Rf", "Cpole"],
        "configuration": [],
    },
    "rlc_series_resonance": {
        "f_r_hz": ["L1", "C1"],
        "Q": ["R1", "L1", "C1"],
        "bandwidth_hz": ["R1", "L1"],
        "Z_at_resonance_ohm": ["R1"],
        "R_ohm": ["R1"],
    },
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class NetlistFact:
    """One unit of information present in the netlist.

    kind:
        ``component`` — a circuit element (designator + params/value)
        ``node``      — a non-ground node
        ``model``     — a device model name (e.g. ``Q2N2222``)
        ``analysis``  — the analysis directive (type + key params)
    """

    kind: str
    name: str
    value: Any = None


@dataclass
class CoverageFailure:
    """A single coverage violation for a topology."""

    kind: str  # missing_component | missing_node | hidden_input | unmapped_fact
    locus: str  # designator / node name / "question_id:input"
    detail: str


@dataclass
class TopologyReport:
    """Coverage result for one topology."""

    family: str
    topology: str
    failures: list[CoverageFailure] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass
class CoverageReport:
    """Aggregate coverage result across topologies."""

    topologies: list[TopologyReport] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(t.passed for t in self.topologies)

    @property
    def failure_count(self) -> int:
        return sum(len(t.failures) for t in self.topologies)

    def to_json(self) -> str:
        payload = {
            "passed": self.passed,
            "failure_count": self.failure_count,
            "topologies": [
                {
                    "family": t.family,
                    "topology": t.topology,
                    "passed": t.passed,
                    "failures": [asdict(f) for f in t.failures],
                }
                for t in self.topologies
            ],
        }
        return json.dumps(payload, indent=2)

    def render_text(self) -> str:
        lines: list[str] = []
        for t in self.topologies:
            status = "PASS" if t.passed else "FAIL"
            lines.append(f"[{status}] {t.topology}")
            for f in t.failures:
                lines.append(f"    - {f.kind}: {f.locus} — {f.detail}")
        total = len(self.topologies)
        passed = sum(1 for t in self.topologies if t.passed)
        lines.append("")
        lines.append(f"{passed}/{total} topologies pass ({self.failure_count} failure(s) total)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Netlist fact derivation
# ---------------------------------------------------------------------------


def _component_value(comp: Any) -> Any:
    """Best-effort scalar value for a component (for reporting)."""
    p = comp.params or {}
    for key in ("value", "dc", "ac"):
        if key in p:
            return p[key]
    return None


def netlist_facts(
    graph: CircuitGraph,
    simulation: Any = None,
) -> list[NetlistFact]:
    """Derive the canonical information content of a circuit graph.

    One fact per component (designator + value), per non-ground node, per
    device model name, and one for the analysis directive. Deterministic and
    simulation-free. ``simulation`` is an optional :class:`SimulationConfig`
    (carried on the ``CircuitRecord``) used to surface the analysis directive.
    """
    facts: list[NetlistFact] = []

    for comp in graph.components:
        facts.append(NetlistFact(kind="component", name=comp.name, value=_component_value(comp)))
        model = (comp.params or {}).get("model")
        if model:
            facts.append(NetlistFact(kind="model", name=model, value=comp.name))

    for node in sorted(graph.non_ground_nodes):
        facts.append(NetlistFact(kind="node", name=node))

    # Analysis directive: prefer the simulation config, else scan raw directives.
    if simulation is not None and getattr(simulation, "type", None):
        facts.append(
            NetlistFact(
                kind="analysis",
                name=f".{simulation.type}",
                value=dict(getattr(simulation, "params", {}) or {}),
            )
        )
    else:
        for line in graph.directives:
            stripped = line.strip().lower()
            if stripped.startswith((".op", ".dc", ".ac", ".tran")):
                facts.append(NetlistFact(kind="analysis", name=line.strip()))
                break

    return facts


# ---------------------------------------------------------------------------
# Image coverage
# ---------------------------------------------------------------------------


def _word_present(name: str, text: str) -> bool:
    """Whether ``name`` appears as a whole token in ``text``.

    Word-boundary matching avoids ``R1`` matching inside ``R12``.
    """
    return re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", text) is not None


def image_present_names(graph: CircuitGraph, template: SVGTemplate) -> set[str]:
    """Component designators that appear in the rendered schematic.

    Renders the template against the graph and reports which component
    designators are visible anywhere in the SVG (slot or plain-text label).
    Matching is case-sensitive and word-bounded so ``R1`` never matches ``R12``.
    """
    svg = fill_template(graph, template)
    return {comp.name for comp in graph.components if _word_present(comp.name, svg)}


def _node_present(node: str, svg: str) -> bool:
    """Whether a node is locatable on the schematic (case-insensitive).

    A supply rail node ``vcc`` is conveyed by the ``VCC`` source label, so node
    presence is matched case-insensitively against the rendered SVG.
    """
    return re.search(rf"(?<![\w]){re.escape(node)}(?![\w])", svg, re.IGNORECASE) is not None


def question_referenced_nodes(graph: CircuitGraph, question_templates: list[dict]) -> set[str]:
    """Non-ground nodes that a question refers to by name.

    A node the solver is asked about (e.g. ``out`` in "voltage at V(out)") must
    be labelled on the schematic so the question is self-contained. Internal
    junction and supply nodes that no question names are conveyed by the wiring
    and need no text label.
    """
    text = " ".join(q.get("question_template", "") for q in question_templates)
    referenced: set[str] = set()
    for node in graph.non_ground_nodes:
        if re.search(rf"(?<![\w]){re.escape(node)}(?![\w])", text, re.IGNORECASE):
            referenced.add(node)
    return referenced


def image_valued_designators(template: SVGTemplate) -> set[str]:
    """Designators whose numeric *value* is shown on the schematic.

    A value is shown when the template declares a ``slot-<REF>`` value slot
    (filled with the formatted component label). Plain-text name labels do not
    count — they convey only the designator, not its value.
    """
    return set(template.value_slots.keys())


# ---------------------------------------------------------------------------
# Question coverage
# ---------------------------------------------------------------------------

_FREQ_RE = re.compile(r"(freq|f_src|_hz)", re.IGNORECASE)


def _designator_of_param(param: str) -> str:
    """Reference designator implied by a parameter key.

    ``R1_ohm`` -> ``R1``, ``Vin_dc`` -> ``Vin``, ``VCC_dc`` -> ``VCC``.
    """
    return param.split("_", 1)[0]


def question_answer_inputs(topology: str, q_entry: dict) -> tuple[set[str], set[str]]:
    """Governing inputs a question's answer depends on.

    Returns ``(inputs, unmapped_facts)`` where ``inputs`` is the set of required
    governing tokens (component designators and/or ``"freq"``), expanded from
    the question's answer-relevant facts through :data:`FACT_INPUTS`, and
    ``unmapped_facts`` lists any answer-relevant fact missing from the table.
    """
    table = FACT_INPUTS.get(topology, {})

    relevant: set[str] = set(q_entry.get("answer_keys", []))
    for op in q_entry.get("program", []):
        if op.get("op") == "read_fact":
            relevant.add(op["fact"])
        elif op.get("op") == "read_param":
            # A read param is itself a governing input.
            relevant.add(op["param"])

    inputs: set[str] = set()
    unmapped: set[str] = set()
    for fact in relevant:
        if fact in table:
            inputs.update(table[fact])
        elif fact.split("_", 1)[0] in {"freq"}:
            inputs.add("freq")
        else:
            # A read_param token maps directly to a designator; otherwise the
            # fact is unmapped and must be added to the table (fail-closed).
            if _looks_like_param(fact):
                inputs.add(_designator_of_param(fact))
            else:
                unmapped.add(fact)
    return inputs, unmapped


def _looks_like_param(name: str) -> bool:
    """Heuristic: a param key like ``R1_ohm`` / ``Vin_dc`` (has a unit suffix)."""
    return bool(re.match(r"^[A-Za-z]+\d*_(ohm|dc|f|h|s|hz|amplitude|frequency)\b", name))


def question_covered_designators(q_entry: dict) -> tuple[set[str], bool]:
    """Inputs conveyed by the question text via ``{param}`` placeholders.

    Returns ``(designators, freq_stated)``.
    """
    text = q_entry.get("question_template", "")
    placeholders = {f[1] for f in string.Formatter().parse(text) if f[1]}
    designators = {_designator_of_param(p) for p in placeholders}
    freq_stated = any(_FREQ_RE.search(p) for p in placeholders)
    return designators, freq_stated


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify_topology(
    family: str,
    topology: str,
    graph: CircuitGraph,
    template: SVGTemplate,
    question_templates: list[dict],
) -> TopologyReport:
    """Run all coverage checks for a single topology."""
    report = TopologyReport(family=family, topology=topology)

    # -- 1. netlist -> image: every component must be drawn ------------------
    present = image_present_names(graph, template)
    for comp in graph.components:
        if comp.name not in present:
            report.failures.append(
                CoverageFailure(
                    kind="missing_component",
                    locus=comp.name,
                    detail=(
                        f"component '{comp.name}' is in the netlist but not drawn in the schematic"
                    ),
                )
            )

    # Every node a question names must be labelled on the schematic.
    svg = fill_template(graph, template)
    for node in sorted(question_referenced_nodes(graph, question_templates)):
        if not _node_present(node, svg):
            report.failures.append(
                CoverageFailure(
                    kind="missing_node",
                    locus=node,
                    detail=(
                        f"node '{node}' is referenced by a question but not "
                        f"labelled in the schematic"
                    ),
                )
            )

    # -- 2. netlist -> (image union question): answer inputs visible ---------
    valued = image_valued_designators(template)
    image_freq = bool(re.search(r"slot-param-(freq|f_src)", template.svg_content))

    for q in question_templates:
        qid = q.get("id", "?")
        inputs, unmapped = question_answer_inputs(topology, q)
        for fact in sorted(unmapped):
            report.failures.append(
                CoverageFailure(
                    kind="unmapped_fact",
                    locus=f"{qid}:{fact}",
                    detail=(
                        f"answer-relevant fact '{fact}' has no entry in "
                        f"FACT_INPUTS['{topology}'] — add its governing inputs"
                    ),
                )
            )

        q_designators, q_freq = question_covered_designators(q)
        for token in sorted(inputs):
            if token == "freq":
                if image_freq or q_freq:
                    continue
                report.failures.append(
                    CoverageFailure(
                        kind="hidden_input",
                        locus=f"{qid}:freq",
                        detail=(
                            "analysis frequency is needed but shown in neither "
                            "the schematic nor the question text"
                        ),
                    )
                )
                continue
            # Component value must be visible in the image or stated in text.
            if token in valued or token in q_designators:
                continue
            report.failures.append(
                CoverageFailure(
                    kind="hidden_input",
                    locus=f"{qid}:{token}",
                    detail=(
                        f"value of '{token}' is needed to answer '{qid}' but "
                        f"is shown in neither the schematic nor the question"
                    ),
                )
            )

    return report


def verify_all(
    registry: TemplateRegistry | None = None,
    *,
    seed: int = 0,
) -> CoverageReport:
    """Verify every registered topology that has both a template and questions.

    Samples each topology at a fixed seed (designators/nodes do not change with
    the sample) and aggregates per-topology reports.
    """
    from ..questions.templates import QUESTION_TEMPLATES
    from ..templates import ALL_TEMPLATES

    reg = registry or default_registry
    report = CoverageReport()

    for template_def in ALL_TEMPLATES:
        topology = template_def.topology
        family = template_def.family
        record = template_def.sample(seed=seed)
        graph = record.graph
        if graph is None or not reg.has_template(graph):
            continue
        svg_template = reg.resolve(graph)
        questions = QUESTION_TEMPLATES.get(topology, [])
        report.topologies.append(verify_topology(family, topology, graph, svg_template, questions))

    return report
