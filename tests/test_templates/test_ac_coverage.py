"""Tests that AC sweep ranges cover theoretical cutoff frequencies."""

from __future__ import annotations

import math

from electronics_qa_generator.templates import RCLowPass, RCHighPass


def _theoretical_cutoff(r_ohm: float, c_f: float) -> float:
    """Compute theoretical -3 dB cutoff frequency for first-order RC circuit."""
    return 1.0 / (2 * math.pi * r_ohm * c_f)


def test_rc_lowpass_cutoff_in_sweep():
    """Theoretical cutoff must fall within the AC sweep range."""
    template = RCLowPass()
    for seed in range(20):
        record = template.sample(seed=seed)
        fc = _theoretical_cutoff(record.parameters["R1_ohm"], record.parameters["C1_f"])
        sim = record.simulation
        assert sim is not None
        start_hz = sim.params["start_hz"]
        stop_hz = sim.params["stop_hz"]
        assert start_hz <= fc <= stop_hz, (
            f"seed={seed}: fc={fc:.1f} not in [{start_hz}, {stop_hz}] "
            f"for R={record.parameters['R1_ohm']}, C={record.parameters['C1_f']}"
        )


def test_rc_highpass_cutoff_in_sweep():
    """Theoretical cutoff must fall within the AC sweep range."""
    template = RCHighPass()
    for seed in range(20):
        record = template.sample(seed=seed)
        fc = _theoretical_cutoff(record.parameters["R1_ohm"], record.parameters["C1_f"])
        sim = record.simulation
        assert sim is not None
        start_hz = sim.params["start_hz"]
        stop_hz = sim.params["stop_hz"]
        assert start_hz <= fc <= stop_hz, (
            f"seed={seed}: fc={fc:.1f} not in [{start_hz}, {stop_hz}] "
            f"for R={record.parameters['R1_ohm']}, C={record.parameters['C1_f']}"
        )
