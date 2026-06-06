"""Tests for validation/template_coverage.py — the question/SVG/netlist triad."""

from __future__ import annotations

import json

from electronics_qa_generator.graph.models import CircuitGraph
from electronics_qa_generator.render.svg_templates import SVGTemplate
from electronics_qa_generator.templates import ALL_TEMPLATES
from electronics_qa_generator.validation.template_coverage import (
    FACT_INPUTS,
    image_valued_designators,
    netlist_facts,
    question_answer_inputs,
    question_covered_designators,
    question_referenced_nodes,
    verify_all,
    verify_topology,
)

_TM = {t.topology: t for t in ALL_TEMPLATES}


# -- Task 1.3: netlist fact derivation ---------------------------------------


class TestNetlistFacts:
    def test_passive_topology_facts(self):
        graph = _TM["voltage_divider"].sample(seed=0).graph
        facts = netlist_facts(graph)

        comp_names = {f.name for f in facts if f.kind == "component"}
        node_names = {f.name for f in facts if f.kind == "node"}

        assert comp_names == {"R1", "R2", "Vin"}
        assert node_names == {"in", "out"}
        # values are carried on component facts
        r1 = next(f for f in facts if f.kind == "component" and f.name == "R1")
        assert r1.value is not None

    def test_transistor_topology_facts_include_model_and_analysis(self):
        record = _TM["bjt_ce_amplifier"].sample(seed=0)
        graph = record.graph
        facts = netlist_facts(graph, record.simulation)

        comp_names = {f.name for f in facts if f.kind == "component"}
        node_names = {f.name for f in facts if f.kind == "node"}
        model_names = {f.name for f in facts if f.kind == "model"}
        analysis = [f for f in facts if f.kind == "analysis"]

        # every component designator appears
        assert {"Q1", "R1", "R2", "RC", "RE", "Rload", "VCC", "Vin"} <= comp_names
        assert {"Cin", "Cout", "Cbypass"} <= comp_names
        # every non-ground node appears
        assert {"base", "collector", "emitter", "in", "out", "vcc"} == node_names
        # device model name surfaced
        assert "Q2N2222" in model_names
        # analysis directive surfaced
        assert analysis and analysis[0].name.lower().startswith(".ac")


# -- Task 2.3: netlist -> image coverage -------------------------------------


class TestImageCoverage:
    def test_all_current_topologies_draw_every_component(self):
        report = verify_all()
        missing = [
            (t.topology, f.locus)
            for t in report.topologies
            for f in t.failures
            if f.kind == "missing_component"
        ]
        assert missing == [], f"components missing from schematics: {missing}"

    def test_missing_component_is_reported_with_locus(self):
        # Build a graph whose template omits one component.
        graph = CircuitGraph(family="passive", topology="toy")
        graph.add_voltage_source("Vin", "in", "0", dc=5)
        graph.add_resistor("R1", "in", "out", 1000)
        graph.add_resistor("R2", "out", "0", 2000)  # not drawn below

        template = SVGTemplate(
            family="passive",
            topology="toy",
            svg_content=(
                '<svg><text id="slot-Vin">Vin</text>'
                '<text id="slot-R1">R1</text>'
                '<text id="slot-node-in">in</text>'
                '<text id="slot-node-out">out</text></svg>'
            ),
        )

        report = verify_topology("passive", "toy", graph, template, [])
        missing = [f for f in report.failures if f.kind == "missing_component"]
        assert len(missing) == 1
        assert missing[0].locus == "R2"
        assert not report.passed


# -- Task 3: question -> fact dependency mapping ------------------------------


class TestQuestionMapping:
    def test_answer_inputs_expand_through_table(self):
        q = {
            "id": "vd_direct_vout",
            "answer_keys": ["Vout_dc"],
            "program": [{"op": "read_fact", "fact": "Vout_dc"}],
        }
        inputs, unmapped = question_answer_inputs("voltage_divider", q)
        assert inputs == {"R1", "R2", "Vin"}
        assert unmapped == set()

    def test_unmapped_fact_is_flagged(self):
        q = {
            "id": "q_bad",
            "answer_keys": ["totally_unknown_fact"],
            "program": [],
        }
        inputs, unmapped = question_answer_inputs("voltage_divider", q)
        assert "totally_unknown_fact" in unmapped

    def test_inlined_placeholder_counts_as_question_coverage(self):
        q = {
            "id": "vd_find_vout_given",
            "question_template": "R1 = {R1_ohm} Ω and R2 = {R2_ohm} Ω, Vin = {Vin_dc} V",
        }
        designators, freq = question_covered_designators(q)
        assert {"R1", "R2", "Vin"} <= designators
        assert freq is False

    def test_frequency_placeholder_detected(self):
        q = {"id": "x", "question_template": "at f = {Vin_frequency_hz} Hz"}
        _, freq = question_covered_designators(q)
        assert freq is True

    def test_table_covers_every_topology_with_questions(self):
        # Every topology that has questions must have a FACT_INPUTS table.
        from electronics_qa_generator.questions.templates import QUESTION_TEMPLATES

        for topo in QUESTION_TEMPLATES:
            assert topo in FACT_INPUTS, f"no FACT_INPUTS entry for {topo}"


# -- Task 4: triad coverage + report -----------------------------------------


class TestTriadCoverage:
    def test_hidden_input_is_reported(self):
        # A question needing a value shown nowhere → hidden_input failure.
        graph = CircuitGraph(family="passive", topology="toy2")
        graph.add_voltage_source("Vin", "in", "0", dc=5)
        graph.add_resistor("R1", "in", "out", 1000)

        # Template draws R1 by NAME only (no value slot) and no question inlines it.
        template = SVGTemplate(
            family="passive",
            topology="toy2",
            svg_content=(
                '<svg><text id="slot-Vin">Vin</text>'
                "<text>R1</text>"  # plain label, no value
                '<text id="slot-node-in">in</text>'
                '<text id="slot-node-out">out</text></svg>'
            ),
        )
        questions = [
            {
                "id": "needs_r1",
                "question_template": "What is V(out)?",
                "answer_keys": ["Vout_dc"],
                "program": [{"op": "read_fact", "fact": "Vout_dc"}],
            }
        ]
        # Map the fact for this toy topology.
        FACT_INPUTS["toy2"] = {"Vout_dc": ["R1", "Vin"]}
        try:
            report = verify_topology("passive", "toy2", graph, template, questions)
        finally:
            del FACT_INPUTS["toy2"]

        hidden = [f for f in report.failures if f.kind == "hidden_input"]
        assert any(f.locus == "needs_r1:R1" for f in hidden)

    def test_report_json_roundtrips(self):
        report = verify_all()
        payload = json.loads(report.to_json())
        assert "passed" in payload
        assert "topologies" in payload
        assert len(payload["topologies"]) >= 1

    def test_referenced_nodes_detection(self):
        graph = _TM["voltage_divider"].sample(seed=0).graph
        qs = [{"question_template": "voltage at V(out) given V(in)"}]
        refd = question_referenced_nodes(graph, qs)
        assert refd == {"in", "out"}


# -- Task 7.1: all-topologies regression -------------------------------------


def test_all_topologies_pass_triad_coverage():
    """Every registered topology's (image + question) conveys all answer inputs.

    This is the standing guard: question template, SVG schematic, and netlist
    must remain mutually consistent for the multimodal QA items to be solvable.
    """
    report = verify_all()
    assert report.passed, "\n" + report.render_text()


def test_value_slots_expose_needed_values():
    """Sanity: image_valued_designators reflects declared value slots."""
    from electronics_qa_generator.render.svg_templates import registry

    graph = _TM["op_amp_inverting"].sample(seed=0).graph
    tpl = registry.resolve(graph)
    assert "Cpole" in image_valued_designators(tpl)
