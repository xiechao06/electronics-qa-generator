"""Tests for deterministic reproducibility of template sampling."""

from __future__ import annotations

from electronics_qa_generator.templates import ALL_TEMPLATES


def test_same_seed_same_output():
    """Same seed must produce identical CircuitRecord."""
    for template in ALL_TEMPLATES:
        record1 = template.sample(seed=42)
        record2 = template.sample(seed=42)

        assert record1.netlist == record2.netlist, (
            f"{template.topology}: netlist differs with same seed"
        )
        assert record1.parameters == record2.parameters, (
            f"{template.topology}: parameters differ with same seed"
        )
        assert record1.family == record2.family
        assert record1.topology == record2.topology
        assert record1.probes == record2.probes
        if record1.simulation is not None:
            assert record1.simulation == record2.simulation


def test_different_seed_different_output():
    """Different seeds must produce different output."""
    for template in ALL_TEMPLATES:
        record1 = template.sample(seed=42)
        record2 = template.sample(seed=43)

        # At least parameters or netlist must differ
        params_differ = record1.parameters != record2.parameters
        netlist_differs = record1.netlist != record2.netlist

        assert params_differ or netlist_differs, (
            f"{template.topology}: same output for seeds 42 and 43"
        )
