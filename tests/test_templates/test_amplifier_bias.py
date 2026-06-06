"""Tests for the active-device amplifier bias samplers.

These templates *design* the bias network from a target operating point so the
transistor lands in its useful region (forward-active for BJTs, saturation for
the MOSFET) instead of being sampled blindly. The checks here assert the
designed parameters place the device in that region across many seeds, without
requiring a simulator.
"""

from __future__ import annotations

from electronics_qa_generator.templates.bjt import BJTCEAmplifier, BJTEFollower
from electronics_qa_generator.templates.e_series import E12_VALUES, snap_e_value
from electronics_qa_generator.templates.mosfet import MOSFETCSAmplifier

_VTO = 2.0


def test_snap_e_value_picks_nearest_standard_value():
    assert snap_e_value(3200.0, E12_VALUES) == 3300.0
    assert snap_e_value(1.0e6, E12_VALUES) == 1.0e6
    assert snap_e_value(95.0, E12_VALUES) == 100.0


class TestBjtCeActiveBias:
    def test_designed_base_voltage_in_active_window(self):
        tpl = BJTCEAmplifier()
        for seed in range(40):
            p = tpl.sample(seed=seed).parameters
            vcc = p["VCC_dc"]
            v_b = vcc * p["R2_ohm"] / (p["R1_ohm"] + p["R2_ohm"])
            v_e = v_b - 0.7
            # Emitter above ground (forward-active) but well below the rail so
            # the collector has headroom -> not saturated, not cut off.
            assert 0.02 * vcc < v_e < 0.30 * vcc, f"seed {seed}: V_E={v_e:.2f} VCC={vcc:.2f}"

    def test_resistors_positive_and_standard(self):
        tpl = BJTCEAmplifier()
        p = tpl.sample(seed=7).parameters
        for key in ("R1_ohm", "R2_ohm", "RC_ohm", "RE_ohm"):
            assert p[key] > 0
            assert snap_e_value(p[key], E12_VALUES) == p[key]


class TestBjtEfActiveBias:
    def test_emitter_near_midrail(self):
        tpl = BJTEFollower()
        for seed in range(40):
            p = tpl.sample(seed=seed).parameters
            vcc = p["VCC_dc"]
            v_b = vcc * p["R2_ohm"] / (p["R1_ohm"] + p["R2_ohm"])
            v_e = v_b - 0.7
            assert 0.2 * vcc < v_e < 0.7 * vcc, f"seed {seed}: V_E={v_e:.2f} VCC={vcc:.2f}"


class TestMosfetSaturationBias:
    def test_gate_divider_params_present(self):
        p = MOSFETCSAmplifier().sample(seed=0).parameters
        assert {"RG1_ohm", "RG2_ohm", "RD_ohm", "RS_ohm", "VDD_dc"} <= set(p)
        assert "RG_ohm" not in p  # single gate resistor is gone

    def test_gate_voltage_exceeds_threshold(self):
        tpl = MOSFETCSAmplifier()
        for seed in range(40):
            p = tpl.sample(seed=seed).parameters
            vdd = p["VDD_dc"]
            v_g = vdd * p["RG2_ohm"] / (p["RG1_ohm"] + p["RG2_ohm"])
            # Gate must sit above V_TO (plus the source drop) for the device to
            # conduct; a comfortable margin keeps it out of cut-off after E12
            # rounding.
            assert v_g > _VTO + 0.5, f"seed {seed}: V_G={v_g:.2f}"

    def test_gate_divider_is_high_impedance(self):
        p = MOSFETCSAmplifier().sample(seed=3).parameters
        assert p["RG1_ohm"] >= 1.0e5
        assert p["RG2_ohm"] >= 1.0e5
