"""Tests for graph/models.py — CircuitGraph construction and queries."""

from __future__ import annotations

from electronics_qa_generator.graph.models import CircuitGraph


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_empty_graph(self):
        g = CircuitGraph()
        assert g.component_count == 0
        assert g.node_count == 0
        assert g.non_ground_nodes == set()

    def test_ground_present_after_adding_component(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5)
        assert "0" in g.nodes
        assert g.node_count == 1  # only "in" besides ground

    def test_node_count_excludes_ground(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "out", 1000)
        g.add_resistor("R2", "out", "0", 2000)
        assert g.node_count == 2  # "in", "out"
        assert g.non_ground_nodes == {"in", "out"}

    def test_component_count(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "out", 1000)
        g.add_resistor("R2", "out", "0", 2000)
        assert g.component_count == 3

    def test_add_resistor_stores_value(self):
        g = CircuitGraph()
        g.add_resistor("R1", "in", "out", 6800)
        c = g.components[0]
        assert c.kind == "resistor"
        assert c.name == "R1"
        assert c.pos == "in"
        assert c.neg == "out"
        assert c.params["value"] == 6800

    def test_add_capacitor(self):
        g = CircuitGraph()
        g.add_capacitor("C1", "in", "out", 1e-7)
        c = g.components[0]
        assert c.kind == "capacitor"
        assert c.params["value"] == 1e-7

    def test_add_inductor(self):
        g = CircuitGraph()
        g.add_inductor("L1", "in", "out", 0.01)
        c = g.components[0]
        assert c.kind == "inductor"
        assert c.params["value"] == 0.01

    def test_add_voltage_source_dc(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5.0)
        c = g.components[0]
        assert c.kind == "vsource"
        assert c.params["dc"] == 5.0

    def test_add_voltage_source_ac(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", ac=1)
        c = g.components[0]
        assert c.params["ac"] == 1

    def test_add_voltage_source_sin(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", sin={"amplitude": 5, "freq": 60})
        c = g.components[0]
        assert c.params["sin"] == {"amplitude": 5, "freq": 60}

    def test_add_voltage_source_dc_and_ac(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5, ac=1)
        c = g.components[0]
        assert "dc" in c.params
        assert "ac" in c.params

    def test_add_diode(self):
        g = CircuitGraph()
        g.add_diode("D1", "in", "out")
        c = g.components[0]
        assert c.kind == "diode"
        assert c.params["model"] == "1N4148"

    def test_add_diode_custom_model(self):
        g = CircuitGraph()
        g.add_diode("D1", "in", "out", model="D1N914")
        c = g.components[0]
        assert c.params["model"] == "D1N914"

    def test_add_directive(self):
        g = CircuitGraph()
        g.add_directive(".model D1N4148 D (Is=2.52n)")
        assert g.directives == [".model D1N4148 D (Is=2.52n)"]

    def test_header_comment(self):
        g = CircuitGraph(header_comment="* Test circuit")
        assert g.header_comment == "* Test circuit"


# ---------------------------------------------------------------------------
# Query methods
# ---------------------------------------------------------------------------


class TestQueries:
    def test_components_by_kind_resistor(self):
        g = CircuitGraph()
        g.add_resistor("R1", "a", "b", 100)
        g.add_capacitor("C1", "b", "0", 1e-6)
        g.add_resistor("R2", "c", "0", 200)
        resistors = g.components_by_kind("resistor")
        assert len(resistors) == 2
        names = {c.name for c in resistors}
        assert names == {"R1", "R2"}

    def test_components_by_kind_empty(self):
        g = CircuitGraph()
        g.add_resistor("R1", "a", "b", 100)
        caps = g.components_by_kind("capacitor")
        assert caps == []

    def test_components_insertion_order(self):
        g = CircuitGraph()
        g.add_resistor("R1", "in", "out", 100)
        g.add_capacitor("C1", "out", "0", 1e-6)
        g.add_resistor("R2", "out", "0", 200)
        names = [c.name for c in g.components]
        assert names == ["R1", "C1", "R2"]
