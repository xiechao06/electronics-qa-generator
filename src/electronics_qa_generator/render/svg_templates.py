"""SVG template registry for circuit schematic rendering.

Maps (family, topology) pairs to hand-authored SVG layout templates
and validates template slots against a CircuitGraph.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import resources

from ..graph.models import CircuitGraph

__all__ = ["TemplateRegistry", "SVGTemplate"]


# -- Slot model ---------------------------------------------------------------

# Stable element id conventions inside SVG templates:
#   id="slot-<REF>"           component value/label slot (e.g. slot-R1)
#   id="slot-node-<NODE>"     node label slot (e.g. slot-node-in)

_SLOT_ID_RE = re.compile(r'\bid="(slot-[\w.\-]+)"')


def _name_in_svg(name: str, svg: str) -> bool:
    """Whether a designator appears as a whole token in raw SVG content.

    Matches slot ids (``slot-R1``) and plain-text labels (``Cin``) while
    word-bounding so ``R1`` never matches inside ``R12``.
    """
    return re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", svg) is not None


@dataclass
class SVGTemplate:
    """A hand-authored SVG layout template with named placeholder slots.

    Slots are text elements identified by stable ``id`` attributes:
    ``slot-R1``, ``slot-node-in``, etc.  The filler replaces their
    text content with formatted component values or node names.
    """

    family: str
    topology: str
    svg_content: str
    _slot_ids: set[str] = field(default_factory=set, repr=False)

    def __post_init__(self) -> None:
        self._slot_ids = self._extract_slot_ids()

    # -- public api -------------------------------------------------------

    @property
    def value_slots(self) -> dict[str, str]:
        """Slots for component values keyed by reference designator.

        Returns ``{"R1": "slot-R1", "Vin": "slot-Vin", ...}``.
        Excludes ``slot-param-*`` and ``slot-node-*`` prefixes.
        """
        return {
            sid.removeprefix("slot-"): sid
            for sid in self._slot_ids
            if not sid.startswith("slot-node-") and not sid.startswith("slot-param-")
        }

    @property
    def node_slots(self) -> dict[str, str]:
        """Slots for node labels keyed by node name.

        Returns ``{"in": "slot-node-in", "out": "slot-node-out", ...}``.
        """
        return {
            sid.removeprefix("slot-node-"): sid
            for sid in self._slot_ids
            if sid.startswith("slot-node-")
        }

    @property
    def all_slot_ids(self) -> set[str]:
        """Full set of SVG element ids that are recognised as slots."""
        return self._slot_ids

    def _extract_slot_ids(self) -> set[str]:
        """Parse the SVG content for ``id=\"slot-...\"`` attributes.

        Uses a simple regex since the templates are hand-authored and
        well-structured — an XML parser is overkill at this point.
        """
        return set(_SLOT_ID_RE.findall(self.svg_content))


# -- Template loading ---------------------------------------------------------

_SVG_RESOURCE_ROOT = "electronics_qa_generator.render.svg"


def load_svg_template(filename: str) -> str:
    """Load an SVG template file via importlib.resources.

    Templates live in ``src/electronics_qa_generator/render/svg/``
    and are shipped with the wheel so they resolve independent of CWD.

    Parameters
    ----------
    filename : str
        Bare filename with extension, e.g. ``"voltage_divider.svg"``.

    Returns
    -------
    str
        Raw SVG content.
    """
    # Use files() + joinpath for importlib.resources >= 3.9 / Python 3.14.
    ref = resources.files(_SVG_RESOURCE_ROOT).joinpath(filename)
    if not ref.is_file():
        raise FileNotFoundError(f"SVG template '{filename}' not found in {_SVG_RESOURCE_ROOT}")
    return ref.read_text(encoding="utf-8")


# -- Registry -----------------------------------------------------------------


class TemplateRegistry:
    """Registry mapping (family, topology) to SVG template files.

    Templates are loaded on demand via importlib.resources and validated
    against CircuitGraph instances before rendering.
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], SVGTemplate] = {}

    # -- registration ----------------------------------------------------

    def register(
        self,
        family: str,
        topology: str,
        filename: str,
    ) -> SVGTemplate:
        """Register a topology and return the loaded template.

        Parameters
        ----------
        family : str
            Circuit family (e.g. ``"passive"``, ``"diode"``).
        topology : str
            Topology name (e.g. ``"voltage_divider"``).
        filename : str
            SVG filename (e.g. ``"voltage_divider.svg"``).

        Returns
        -------
        SVGTemplate
            The loaded and validated template.
        """
        svg_content = load_svg_template(filename)
        tpl = SVGTemplate(family=family, topology=topology, svg_content=svg_content)
        self._entries[(family, topology)] = tpl
        return tpl

    def get(self, family: str, topology: str) -> SVGTemplate | None:
        """Return the template for a topology, or None."""
        return self._entries.get((family, topology))

    # -- graph-based lookup -----------------------------------------------

    def has_template(self, graph: CircuitGraph | None) -> bool:
        """Check whether a topology has a registered SVG template.

        Requires that the graph carries ``family`` and ``topology``
        attributes (set by the template sampler that produced it).
        """
        if graph is None:
            return False
        fam = getattr(graph, "family", None)
        top = getattr(graph, "topology", None)
        if fam is None or top is None:
            return False
        return (fam, top) in self._entries

    def resolve(self, graph: CircuitGraph) -> SVGTemplate:
        """Resolve and validate a template for the given graph.

        Raises
        ------
        KeyError
            If no template is registered for this topology.
        ValueError
            If the template slots don't match the graph's components/nodes.
        """
        fam = getattr(graph, "family", None)
        top = getattr(graph, "topology", None)
        if fam is None or top is None:
            raise KeyError(
                "CircuitGraph must carry 'family' and 'topology' attributes "
                "to resolve an SVG template"
            )
        key = (fam, top)
        tpl = self._entries.get(key)
        if tpl is None:
            raise KeyError(f"No SVG template registered for family={fam!r} topology={top!r}")
        self._validate(tpl, graph)
        return tpl

    # -- validation -------------------------------------------------------

    def _validate(self, template: SVGTemplate, graph: CircuitGraph) -> None:
        """Check template slots match graph components and nodes.

        Raises ValueError with a descriptive message on mismatch.
        """
        # Component designators expected by the template
        expected_refs = set(template.value_slots.keys())
        actual_refs = {c.name for c in graph.components}

        missing = expected_refs - actual_refs

        if missing:
            # Resolve source naming aliases: if template declares "Vin" but
            # graph uses "V1" (or vice versa), that's not a real mismatch.
            unresolved = set()
            for ref in missing:
                # Normalize: if template has "Vin" or "V1" and graph has the other
                candidates = {ref, ref.replace("Vin", "V1").replace("V1", "Vin")}
                if not (candidates & actual_refs):
                    unresolved.add(ref)
            if unresolved:
                raise ValueError(
                    f"Template '{template.topology}' expects component slots "
                    f"{sorted(unresolved)} but graph has designators "
                    f"{sorted(actual_refs)}"
                )

        # Node slots
        expected_nodes = set(template.node_slots.keys())
        actual_nodes = graph.non_ground_nodes
        missing_nodes = expected_nodes - actual_nodes
        if missing_nodes:
            raise ValueError(
                f"Template '{template.topology}' expects node slots "
                f"{sorted(missing_nodes)} but graph has non-ground nodes "
                f"{sorted(actual_nodes)}"
            )

        # Bidirectional component coverage: every graph component must be
        # represented in the template (value/label slot or visible text label),
        # so an incomplete schematic that silently omits a part is rejected
        # before any PNG is produced.
        undrawn = [
            c.name for c in graph.components if not _name_in_svg(c.name, template.svg_content)
        ]
        if undrawn:
            raise ValueError(
                f"Template '{template.topology}' does not draw component(s) "
                f"{sorted(undrawn)} that are present in the netlist; every "
                f"component must appear in the schematic"
            )

    def clear(self) -> None:
        """Remove all registrations (useful for testing)."""
        self._entries.clear()


# -- module-level convenience ------------------------------------------------

# Top-level registry instance used by the renderer.
registry = TemplateRegistry()


# -- Default MVP registrations ---------------------------------------------


def _register_defaults() -> None:
    """Register the 5 MVP topology templates."""
    registry.register("passive", "voltage_divider", "voltage_divider.svg")
    registry.register("passive", "rc_lowpass", "rc_lowpass.svg")
    registry.register("passive", "rc_highpass", "rc_highpass.svg")
    registry.register("passive", "rlc_bandpass", "rlc_bandpass.svg")
    registry.register("diode", "half_wave_rectifier", "half_wave_rectifier.svg")
    registry.register("passive", "rc_step_response", "rc_step_response.svg")
    registry.register("passive", "rl_step_response", "rl_step_response.svg")
    registry.register("passive", "ac_phasor_rc", "ac_phasor_rc.svg")
    registry.register("transistor", "bjt_ce_amplifier", "bjt_ce_amplifier.svg")
    registry.register("transistor", "bjt_emitter_follower", "bjt_emitter_follower.svg")
    registry.register("transistor", "mosfet_cs_amplifier", "mosfet_cs_amplifier.svg")
    registry.register("passive", "resistor_network", "resistor_network.svg")
    registry.register("opamp", "op_amp_inverting", "op_amp_inverting.svg")
    registry.register("passive", "rlc_series_resonance", "rlc_series_resonance.svg")
    registry.register("passive", "dc_multisource_mesh", "dc_multisource_mesh.svg")
    registry.register("opamp", "op_amp_inv_input_fb", "op_amp_inv_input_fb.svg")


_register_defaults()
