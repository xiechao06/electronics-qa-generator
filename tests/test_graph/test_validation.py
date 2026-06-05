"""Tests for CircuitGraph.validate() — pre-simulation sanity checks."""

from __future__ import annotations

from electronics_qa_generator.graph.models import CircuitGraph


def _make_valid_graph() -> CircuitGraph:
    g = CircuitGraph()
    g.add_voltage_source("Vin", "in", "0", dc=5)
    g.add_resistor("R1", "in", "out", 1000)
    g.add_resistor("R2", "out", "0", 2000)
    return g


class TestValidCircuit:
    def test_no_errors(self):
        g = _make_valid_graph()
        errors = g.validate()
        assert errors == []

    def test_header_comment_optional(self):
        g = _make_valid_graph()
        g.header_comment = None
        errors = g.validate()
        assert errors == []


class TestNoSource:
    def test_no_source_reported(self):
        g = CircuitGraph()
        g.add_resistor("R1", "in", "out", 1000)
        g.add_resistor("R2", "out", "0", 2000)
        errors = g.validate()
        assert len(errors) >= 1
        assert any("no voltage source" in e.lower() for e in errors)


class TestFloatingNode:
    def test_floating_node_reported(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "out", 1000)
        # R2 is missing → "out" has only 1 connection
        errors = g.validate()
        assert len(errors) >= 1
        assert any("floating" in e.lower() and "out" in e for e in errors)

    def test_ground_not_flagged_as_floating(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5)
        # Only Vin connects to ground - "0", "in" both degree 1
        # But ground is excluded from floating check
        errors = g.validate()
        # "in" has degree 1 → floating
        assert any("in" in e for e in errors)
        # "0" should not be in any error
        assert not any("'0'" in e and "floating" in e.lower() for e in errors)


class TestMissingGround:
    def test_missing_ground_reported(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "gnd", dc=5)
        g.add_resistor("R1", "in", "gnd", 1000)
        errors = g.validate()
        assert any("ground" in e.lower() for e in errors)


class TestUnknownNode:
    def test_unknown_node_reported(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "out", 1000)
        # "in", "out", "0" are registered, but R2 references "mid" (not registered)
        from electronics_qa_generator.graph.models import Component

        g.components.append(
            Component(name="R2", kind="resistor", pos="mid", neg="0", params={"value": 2000}),
        )
        errors = g.validate()
        assert any("mid" in e for e in errors)


class TestDuplicateNames:
    def test_duplicate_name_reported(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "out", 1000)
        # Add another component with same name
        g.components.append(
            type(g.components[0])(
                name="R1",
                kind="resistor",
                pos="out",
                neg="0",
                params={"value": 2000},
            ),
        )
        errors = g.validate()
        assert any("duplicate" in e.lower() for e in errors)
