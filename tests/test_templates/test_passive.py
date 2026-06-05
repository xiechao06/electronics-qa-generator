"""Tests for passive circuit templates."""

from __future__ import annotations

from electronics_qa_generator.templates import (
    RCLowPass,
    RCHighPass,
    RLCBandPass,
    VoltageDivider,
)


# ---------------------------------------------------------------------------
# VoltageDivider
# ---------------------------------------------------------------------------


def test_voltage_divider_basics():
    record = VoltageDivider().sample(seed=42)
    assert record.family == "passive"
    assert record.topology == "voltage_divider"
    assert record.difficulty == 1
    assert record.simulation is not None
    assert record.simulation.type == "op"

    # Parameters
    assert "R1_ohm" in record.parameters
    assert "R2_ohm" in record.parameters
    assert "Vin_dc" in record.parameters
    assert 100 <= record.parameters["R1_ohm"] <= 8.2e6
    assert 100 <= record.parameters["R2_ohm"] <= 8.2e6
    assert 1.0 <= record.parameters["Vin_dc"] <= 30.0

    # Netlist
    assert record.netlist.startswith("*")
    assert ".op" in record.netlist
    assert "R1" in record.netlist
    assert "R2" in record.netlist
    assert ".end" in record.netlist.splitlines()[-1]

    # Probes
    assert "V(out)" in record.probes


def test_voltage_divider_vary():
    records = [VoltageDivider().sample(seed=i) for i in range(3)]
    # At least one parameter differs across seeds
    params = [
        (r.parameters["R1_ohm"], r.parameters["R2_ohm"], r.parameters["Vin_dc"]) for r in records
    ]
    assert len(set(params)) == 3  # all three should be different


# ---------------------------------------------------------------------------
# RC Low-pass
# ---------------------------------------------------------------------------


def test_rc_lowpass_basics():
    record = RCLowPass().sample(seed=42)
    assert record.family == "passive"
    assert record.topology == "rc_lowpass"
    assert record.difficulty == 1
    assert record.simulation is not None
    assert record.simulation.type == "ac"
    assert record.simulation.params["start_hz"] == 0.01
    assert record.simulation.params["stop_hz"] == 10_000_000
    assert record.simulation.params["points_per_decade"] == 50

    # Parameters
    assert "R1_ohm" in record.parameters
    assert "C1_f" in record.parameters
    assert 1000 <= record.parameters["R1_ohm"] <= 8.2e6  # min base=1.0, min decade=3 → 1k
    assert 1e-9 <= record.parameters["C1_f"] <= 6.8e-6  # decades −9 to −6

    # Netlist topology check
    assert "R1" in record.netlist
    assert "C1" in record.netlist
    assert "AC 1" in record.netlist
    assert ".ac dec 50" in record.netlist
    assert ".end" in record.netlist.splitlines()[-1]

    # Probes
    assert "V(out)" in record.probes


# ---------------------------------------------------------------------------
# RC High-pass
# ---------------------------------------------------------------------------


def test_rc_highpass_basics():
    record = RCHighPass().sample(seed=42)
    assert record.family == "passive"
    assert record.topology == "rc_highpass"
    assert record.simulation is not None
    assert record.simulation.type == "ac"

    # Parameters
    assert "R1_ohm" in record.parameters
    assert "C1_f" in record.parameters

    # Netlist: capacitor in series with input, resistor to ground
    lines = record.netlist.splitlines()
    assert any("C1" in line and "in" in line for line in lines), "C1 must be connected to input"
    assert any("R1" in line and " 0" in line for line in lines), "R1 must be connected to ground"


# ---------------------------------------------------------------------------
# RLC Band-pass
# ---------------------------------------------------------------------------


def test_rlc_bandpass_basics():
    record = RLCBandPass().sample(seed=42)
    assert record.family == "passive"
    assert record.topology == "rlc_bandpass"
    assert record.difficulty == 1
    assert record.simulation is not None
    assert record.simulation.type == "ac"
    assert record.simulation.params["start_hz"] == 10

    # Parameters
    assert "R1_ohm" in record.parameters
    assert "L1_h" in record.parameters
    assert "C1_f" in record.parameters
    assert 100 <= record.parameters["R1_ohm"] <= 8.2e4
    assert 1e-3 <= record.parameters["L1_h"] <= 1e-1
    assert 1e-8 <= record.parameters["C1_f"] <= 6.8e-6

    # Netlist: series RLC with output across R
    assert "L1" in record.netlist
    assert "C1" in record.netlist
    assert "R1" in record.netlist
    assert ".ac dec 50" in record.netlist
    assert ".end" in record.netlist.splitlines()[-1]
