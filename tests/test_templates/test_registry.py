"""Tests for the ALL_TEMPLATES registry."""

from __future__ import annotations

from electronics_qa_generator.templates import ALL_TEMPLATES
from electronics_qa_generator.templates.base import CircuitTemplate


def test_registry_has_fourteen_items():
    assert len(ALL_TEMPLATES) == 16


def test_registry_distinct_topologies():
    topologies = {t.topology for t in ALL_TEMPLATES}
    assert len(topologies) == 16
    expected = {
        "voltage_divider",
        "rc_lowpass",
        "rc_highpass",
        "rlc_bandpass",
        "half_wave_rectifier",
        "rc_step_response",
        "rl_step_response",
        "ac_phasor_rc",
        "bjt_ce_amplifier",
        "bjt_emitter_follower",
        "mosfet_cs_amplifier",
        "resistor_network",
        "op_amp_inverting",
        "rlc_series_resonance",
        "dc_multisource_mesh",
        "op_amp_inv_input_fb",
    }
    assert topologies == expected


def test_registry_all_are_circuit_templates():
    for t in ALL_TEMPLATES:
        assert isinstance(t, CircuitTemplate)
