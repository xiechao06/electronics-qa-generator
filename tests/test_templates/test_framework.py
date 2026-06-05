"""Tests for the template framework: base class, distributions, E-series, netlist."""

from __future__ import annotations

import random

import pytest

from electronics_qa_generator.models import CircuitRecord
from electronics_qa_generator.templates.base import CircuitTemplate
from electronics_qa_generator.templates.e_series import (
    E12_VALUES,
    E6_VALUES,
    INDUCTOR_VALUES,
    pick_e_value,
)
from electronics_qa_generator.templates.netlist_helpers import format_netlist
from electronics_qa_generator.templates.parameter import Choice, LogUniform, Uniform


# ---------------------------------------------------------------------------
# CircuitTemplate ABC enforcement
# ---------------------------------------------------------------------------


def test_abc_requires_sample():
    """Instantiating a subclass without sample() raises TypeError."""

    class Incomplete(CircuitTemplate):
        family = "test"
        topology = "incomplete"

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_abc_allows_concrete():
    """A concrete subclass with sample() instantiates fine."""

    class Concrete(CircuitTemplate):
        family = "test"
        topology = "concrete"

        def sample(self, seed: int | None = None) -> CircuitRecord:
            return CircuitRecord(
                id="test_id",
                family=self.family,
                topology=self.topology,
                difficulty=1,
                netlist=".op\n.end",
                probes=["V(out)"],
            )

    inst = Concrete()
    assert inst.family == "test"
    assert inst.topology == "concrete"
    record = inst.sample(seed=42)
    assert record.netlist == ".op\n.end"


# ---------------------------------------------------------------------------
# Distribution bounds and determinism
# ---------------------------------------------------------------------------


def test_uniform_bounds():
    dist = Uniform(1e3, 1e6)
    rng = random.Random(42)
    for _ in range(100):
        v = dist.sample(rng)
        assert 1e3 <= v <= 1e6


def test_uniform_rejects_invalid():
    with pytest.raises(ValueError):
        Uniform(10, 1)


def test_loguniform_bounds():
    dist = LogUniform(1e-10, 1e-6)
    rng = random.Random(42)
    for _ in range(100):
        v = dist.sample(rng)
        assert 1e-10 <= v <= 1e-6


def test_loguniform_spans_orders():
    """LogUniform(1e-10, 1e-6) should span at least 2 orders over 1000 samples."""
    dist = LogUniform(1e-10, 1e-6)
    values = {dist.sample(random.Random(i)) for i in range(1000)}
    log_vals = [v for v in values]
    span = max(log_vals) / min(log_vals)
    assert span >= 100  # at least 2 orders of magnitude


def test_loguniform_rejects_non_positive():
    with pytest.raises(ValueError):
        LogUniform(-1, 10)


def test_choice_samples():
    dist = Choice([1.0, 2.0, 3.0])
    rng = random.Random(42)
    for _ in range(20):
        assert dist.sample(rng) in [1.0, 2.0, 3.0]


def test_choice_rejects_empty():
    with pytest.raises(ValueError):
        Choice([])


def test_distribution_determinism():
    """Same rng state -> same value."""
    dist = Uniform(0, 100)
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    assert dist.sample(rng1) == dist.sample(rng2)


# ---------------------------------------------------------------------------
# E-series values
# ---------------------------------------------------------------------------


def test_e6_values():
    assert E6_VALUES == [1.0, 1.5, 2.2, 3.3, 4.7, 6.8]


def test_e12_values():
    assert E12_VALUES == [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]


def test_inductor_values():
    assert len(INDUCTOR_VALUES) > 0
    assert all(v > 0 for v in INDUCTOR_VALUES)


def test_pick_e_value_range():
    rng = random.Random(42)
    for _ in range(50):
        v = pick_e_value(E12_VALUES, decade_min=2, decade_max=6, rng=rng)
        assert 100 <= v <= 8.2e6  # 1.0 * 10^2 to 8.2 * 10^6

    for i in range(50):
        v = pick_e_value(E6_VALUES, decade_min=-10, decade_max=-5, rng=random.Random(i + 100))
        assert 1e-10 <= v <= 6.8e-5


# ---------------------------------------------------------------------------
# format_netlist
# ---------------------------------------------------------------------------


def test_format_netlist_basic():
    result = format_netlist("R1 in out {R1_val}\n.op\n.end", {"R1_val": "18.2k"})
    assert "18.2k" in result
    assert result.endswith(".end")
