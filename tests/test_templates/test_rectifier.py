"""Tests for rectifier circuit template."""

from __future__ import annotations

from electronics_qa_generator.templates import HalfWaveRectifier


def test_half_wave_rectifier_basics():
    record = HalfWaveRectifier().sample(seed=42)
    assert record.family == "diode"
    assert record.topology == "half_wave_rectifier"
    assert record.difficulty == 1
    assert record.simulation is not None
    assert record.simulation.type == "tran"

    # Parameters
    assert "R_load_ohm" in record.parameters
    assert "C_filter_f" in record.parameters
    assert "Vin_amplitude" in record.parameters
    assert "Vin_frequency_hz" in record.parameters
    assert 1000 <= record.parameters["R_load_ohm"] <= 8.2e5
    assert 1e-6 <= record.parameters["C_filter_f"] <= 6.8e-4
    assert 1.0 <= record.parameters["Vin_amplitude"] <= 20.0
    assert record.parameters["Vin_frequency_hz"] == 60.0

    # Netlist checks
    assert "D1" in record.netlist
    assert "D1N4148" in record.netlist  # diode model
    assert ".tran" in record.netlist
    assert ".end" in record.netlist.splitlines()[-1]

    # Probes
    assert "V(out)" in record.probes

    # Simulation params
    assert "stop_time" in record.simulation.params
    assert "time_step" in record.simulation.params


def test_half_wave_rectifier_stop_time():
    """stop_time must be >= 10 source periods (>= ~167ms for 60Hz)."""
    record = HalfWaveRectifier().sample(seed=42)
    stop_time = record.simulation.params["stop_time"]
    assert stop_time >= 10 / 60.0  # ≈ 0.167 s


def test_half_wave_rectifier_vary():
    records = [HalfWaveRectifier().sample(seed=i) for i in range(3)]
    params = [
        (r.parameters["R_load_ohm"], r.parameters["C_filter_f"], r.parameters["Vin_amplitude"])
        for r in records
    ]
    assert len(set(params)) == 3
