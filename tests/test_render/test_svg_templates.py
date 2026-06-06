"""Tests for render/svg_templates.py — registry, loading, validation."""

from __future__ import annotations

import pytest

from electronics_qa_generator.graph.models import CircuitGraph
from electronics_qa_generator.render.svg_templates import (
    SVGTemplate,
    TemplateRegistry,
    load_svg_template,
    registry as default_registry,
)


# -- Helpers ------------------------------------------------------------------


def _make_graph(family: str, topology: str, refs: list[tuple[str, str, str, str]]) -> CircuitGraph:
    """Build a graph with resistor components at given refs.

    Each entry: (kind, name, pos, neg).
    """
    g = CircuitGraph(family=family, topology=topology)
    for kind, name, p, n in refs:
        if kind == "vsource":
            g.add_voltage_source(name, p, n, dc=5)
        elif kind == "resistor":
            g.add_resistor(name, p, n, 1000)
        elif kind == "capacitor":
            g.add_capacitor(name, p, n, 1e-7)
        elif kind == "inductor":
            g.add_inductor(name, p, n, 0.01)
        elif kind == "diode":
            g.add_diode(name, p, n)
    return g


# -- Task 6.1: Registry resolution -------------------------------------------


class TestRegistryResolution:
    def test_known_topology_resolves_template(self):
        """A registered topology returns a template with correct family/topology."""
        g = _make_graph(
            "passive",
            "voltage_divider",
            [
                ("vsource", "Vin", "in", "0"),
                ("resistor", "R1", "in", "out"),
                ("resistor", "R2", "out", "0"),
            ],
        )
        tpl = default_registry.resolve(g)
        assert tpl.family == "passive"
        assert tpl.topology == "voltage_divider"
        assert "slot-R1" in tpl.all_slot_ids

    def test_unknown_topology_has_no_template(self):
        """has_template returns False for unregistered topology."""
        g = _make_graph("custom", "unknown_topology", [("resistor", "R1", "in", "out")])
        assert default_registry.has_template(g) is False

    def test_unknown_topology_resolve_raises(self):
        """resolve raises KeyError for unregistered topology."""
        g = _make_graph("custom", "unknown_topology", [("resistor", "R1", "in", "out")])
        with pytest.raises(KeyError):
            default_registry.resolve(g)

    def test_all_mvp_topologies_have_template(self):
        """Every MVP topology has a registered template."""
        mvp = [
            ("passive", "voltage_divider"),
            ("passive", "rc_lowpass"),
            ("passive", "rc_highpass"),
            ("passive", "rlc_bandpass"),
            ("diode", "half_wave_rectifier"),
        ]
        for family, topology in mvp:
            g = CircuitGraph(family=family, topology=topology)
            assert default_registry.has_template(g), f"Missing template for {family}/{topology}"


# -- Task 6.2: Slot/graph validation -----------------------------------------


class TestSlotValidation:
    def test_mismatched_component_rejected(self):
        """Template with slots not matching graph components raises ValueError."""
        registry = TemplateRegistry()
        svg = '<svg><text id="slot-R1">R1</text><text id="slot-C1">C1</text></svg>'
        # Override load to avoid file dependency
        registry._entries[("test", "mismatch")] = SVGTemplate(
            family="test", topology="mismatch", svg_content=svg
        )
        g = _make_graph("test", "mismatch", [("resistor", "R1", "in", "out")])
        with pytest.raises(ValueError, match="C1"):
            registry.resolve(g)

    def test_valid_graph_passes_validation(self):
        """Graph matching template slots passes validation."""
        g = _make_graph(
            "passive",
            "voltage_divider",
            [
                ("vsource", "Vin", "in", "0"),
                ("resistor", "R1", "in", "out"),
                ("resistor", "R2", "out", "0"),
            ],
        )
        tpl = default_registry.resolve(g)
        assert "slot-R1" in tpl.all_slot_ids


class TestBidirectionalCoverage:
    """Every graph component must be drawn, not just declared slots matched."""

    def test_undrawn_component_is_rejected(self):
        g = _make_graph(
            "passive",
            "toy_missing",
            [
                ("vsource", "Vin", "in", "0"),
                ("resistor", "R1", "in", "out"),
                ("resistor", "R2", "out", "0"),
            ],
        )
        reg = TemplateRegistry()
        # Template draws Vin and R1 but omits R2 entirely.
        reg._entries[("passive", "toy_missing")] = SVGTemplate(
            family="passive",
            topology="toy_missing",
            svg_content=(
                '<svg><text id="slot-Vin">Vin</text>'
                '<text id="slot-R1">R1</text>'
                '<text id="slot-node-in">in</text>'
                '<text id="slot-node-out">out</text></svg>'
            ),
        )
        with pytest.raises(ValueError, match="R2"):
            reg.resolve(g)

    def test_all_registered_topologies_resolve(self):
        from electronics_qa_generator.templates import ALL_TEMPLATES

        for template in ALL_TEMPLATES:
            graph = template.sample(seed=0).graph
            if default_registry.has_template(graph):
                default_registry.resolve(graph)  # must not raise


# -- Task 6.3: Loading via importlib.resources --------------------------------


class TestTemplateLoading:
    def test_load_valid_template(self):
        """Loading a real template file returns SVG content."""
        content = load_svg_template("voltage_divider.svg")
        assert "<svg" in content
        assert "slot-Vin" in content
        assert "</svg>" in content

    def test_load_missing_template_raises(self):
        """Loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_svg_template("nonexistent.svg")


# -- Schematic completeness ---------------------------------------------------
#
# The "every netlist component must be drawn" guarantee is now enforced two ways:
#   * at render time by TemplateRegistry._validate (bidirectional coverage), and
#   * across all topologies by
#     tests/test_validation/test_template_coverage.py.
# See TestBidirectionalCoverage above and the triad-coverage regression there.
