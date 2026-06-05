"""Tests for graph/spice_emitter.py — SPICE netlist emission."""

from __future__ import annotations

from electronics_qa_generator.graph.models import CircuitGraph
from electronics_qa_generator.models import SimulationConfig


def _make_divider() -> CircuitGraph:
    g = CircuitGraph(header_comment="* Voltage divider")
    g.add_voltage_source("Vin", "in", "0", dc=5.0)
    g.add_resistor("R1", "in", "out", 1000)
    g.add_resistor("R2", "out", "0", 2000)
    return g


def _make_rc_lowpass() -> CircuitGraph:
    g = CircuitGraph(header_comment="* RC low-pass")
    g.add_voltage_source("Vin", "in", "0", ac=1)
    g.add_resistor("R1", "in", "out", 6800)
    g.add_capacitor("C1", "out", "0", 1e-7)
    return g


# ---------------------------------------------------------------------------
# .op simulation
# ---------------------------------------------------------------------------


class TestOpEmission:
    def test_contains_op_card(self):
        g = _make_divider()
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert ".op" in netlist

    def test_contains_print_op(self):
        g = _make_divider()
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert ".print dc" in netlist

    def test_ends_with_end(self):
        g = _make_divider()
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert netlist.endswith(".end")

    def test_components_in_insertion_order(self):
        g = _make_divider()
        netlist = g.to_spice(SimulationConfig(type="op"))
        lines = netlist.splitlines()
        # Vin should come before R1 before R2
        vin_idx = next(i for i, line in enumerate(lines) if line.startswith("Vin"))
        r1_idx = next(i for i, line in enumerate(lines) if line.startswith("R1"))
        r2_idx = next(i for i, line in enumerate(lines) if line.startswith("R2"))
        assert vin_idx < r1_idx < r2_idx

    def test_header_comment_first_line(self):
        g = _make_divider()
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert netlist.splitlines()[0] == "* Voltage divider"


# ---------------------------------------------------------------------------
# .ac simulation
# ---------------------------------------------------------------------------


class TestAcEmission:
    def test_contains_ac_card(self):
        g = _make_rc_lowpass()
        netlist = g.to_spice(
            SimulationConfig(
                type="ac",
                params={"start_hz": 1, "stop_hz": 1_000_000, "points_per_decade": 50},
            ),
        )
        assert ".ac dec 50" in netlist

    def test_contains_print_ac(self):
        g = _make_rc_lowpass()
        netlist = g.to_spice(
            SimulationConfig(
                type="ac",
                params={"start_hz": 1, "stop_hz": 1_000_000, "points_per_decade": 50},
            ),
        )
        assert ".print ac" in netlist

    def test_ac_frequency_formatting(self):
        g = _make_rc_lowpass()
        netlist = g.to_spice(
            SimulationConfig(
                type="ac",
                params={"start_hz": 0.01, "stop_hz": 10_000_000, "points_per_decade": 50},
            ),
        )
        assert "0.01" in netlist
        assert "10Meg" in netlist


# ---------------------------------------------------------------------------
# .tran simulation
# ---------------------------------------------------------------------------


class TestTranEmission:
    def test_contains_tran_card(self):
        g = CircuitGraph(header_comment="* Test")
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "0", 1000)
        netlist = g.to_spice(
            SimulationConfig(
                type="tran",
                params={"time_step": 1e-5, "stop_time": 0.1},
            ),
        )
        assert ".tran" in netlist

    def test_contains_print_tran(self):
        g = CircuitGraph(header_comment="* Test")
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "0", 1000)
        netlist = g.to_spice(
            SimulationConfig(
                type="tran",
                params={"time_step": 1e-5, "stop_time": 0.1},
            ),
        )
        assert ".print tran" in netlist


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------


class TestValueFormatting:
    def test_resistor_kilo(self):
        g = CircuitGraph()
        g.add_resistor("R1", "a", "b", 6800)
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert "6.8k" in netlist

    def test_resistor_meg(self):
        g = CircuitGraph()
        g.add_resistor("R1", "a", "b", 1_000_000)
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert "1Meg" in netlist

    def test_resistor_plain(self):
        g = CircuitGraph()
        g.add_resistor("R1", "a", "b", 100)
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert "R1 a b 100" in netlist

    def test_capacitor_nano(self):
        g = CircuitGraph()
        g.add_capacitor("C1", "a", "b", 1e-7)
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert "100n" in netlist

    def test_capacitor_micro(self):
        g = CircuitGraph()
        g.add_capacitor("C1", "a", "b", 1e-4)
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert "100u" in netlist

    def test_inductor_milli(self):
        g = CircuitGraph()
        g.add_inductor("L1", "a", "b", 0.001)
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert "1m" in netlist


# ---------------------------------------------------------------------------
# Directives and VSIN
# ---------------------------------------------------------------------------


class TestDirectives:
    def test_model_directive_emitted(self):
        g = CircuitGraph(header_comment="* Rectifier")
        g.add_voltage_source("Vin", "in", "0", sin={"amplitude": 5, "freq": 60})
        g.add_diode("D1", "in", "out")
        g.add_directive(".model D1N4148 D (Is=2.52n)")
        netlist = g.to_spice(
            SimulationConfig(type="tran", params={"stop_time": 0.1}),
        )
        assert ".model D1N4148 D (Is=2.52n)" in netlist

    def test_sin_formatting(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", sin={"amplitude": 5, "freq": 60})
        netlist = g.to_spice(SimulationConfig(type="tran", params={"stop_time": 0.1}))
        assert "SIN(0 5 60 0 0)" in netlist


# ---------------------------------------------------------------------------
# print_signals
# ---------------------------------------------------------------------------


class TestPrintSignals:
    def test_default_print_signals(self):
        g = _make_divider()
        netlist = g.to_spice(SimulationConfig(type="op"))
        assert "V(out)" in netlist

    def test_custom_print_signals(self):
        g = _make_divider()
        netlist = g.to_spice(
            SimulationConfig(type="op"),
            print_signals=["V(in)", "I(R1)"],
        )
        assert ".print dc V(in) I(R1)" in netlist

    def test_multiple_signals(self):
        g = _make_divider()
        netlist = g.to_spice(
            SimulationConfig(type="op"),
            print_signals=["V(out)", "V(in)"],
        )
        assert ".print dc V(out) V(in)" in netlist
