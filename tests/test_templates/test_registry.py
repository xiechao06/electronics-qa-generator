"""Tests for the ALL_TEMPLATES registry."""

from __future__ import annotations

from electronics_qa_generator.templates import ALL_TEMPLATES
from electronics_qa_generator.templates.base import CircuitTemplate


def test_registry_has_five_items():
    assert len(ALL_TEMPLATES) == 5


def test_registry_distinct_topologies():
    topologies = {t.topology for t in ALL_TEMPLATES}
    assert len(topologies) == 5
    assert topologies == {
        "voltage_divider",
        "rc_lowpass",
        "rc_highpass",
        "rlc_bandpass",
        "half_wave_rectifier",
    }


def test_registry_all_are_circuit_templates():
    for t in ALL_TEMPLATES:
        assert isinstance(t, CircuitTemplate)
