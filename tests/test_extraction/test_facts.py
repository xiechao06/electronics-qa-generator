"""Tests for extraction/facts.py — fact extractors."""

from __future__ import annotations

import pytest

from electronics_qa_generator.extraction.facts import (
    FACT_EXTRACTORS,
    _classify_behavior,
    find_cutoff_frequency,
)


# ---------------------------------------------------------------------------
# find_cutoff_frequency
# ---------------------------------------------------------------------------


class TestFindCutoffFrequency:
    def test_lowpass_cutoff(self):
        freqs = [1, 10, 100, 1000, 10000]
        # passband gain ≈ 0 dB, drops at fc ≈ 1000 Hz
        gains = [0.0, -0.1, -0.5, -3.0, -20.0]
        fc = find_cutoff_frequency(freqs, gains)
        # Should be near the −3 dB crossing
        assert 500 < fc < 2000

    def test_highpass_cutoff(self):
        freqs = [1, 10, 100, 1000, 10000]
        # starts low, rises to 0 dB
        gains = [-20.0, -3.0, -0.5, -0.1, 0.0]
        fc = find_cutoff_frequency(freqs, gains)
        assert 5 < fc < 500

    def test_no_cutoff_returns_zero(self):
        # All gains same → no −3 dB point
        freqs = [1, 10, 100]
        gains = [0.0, 0.0, 0.0]
        assert find_cutoff_frequency(freqs, gains) == 0.0

    def test_empty_lists(self):
        assert find_cutoff_frequency([], []) == 0.0


# ---------------------------------------------------------------------------
# _classify_behavior
# ---------------------------------------------------------------------------


class TestClassifyBehavior:
    def test_lowpass(self):
        gains = [0.0, -3.0, -10.0, -20.0, -30.0]
        assert _classify_behavior(gains, 1000.0) == "low-pass"

    def test_highpass(self):
        gains = [-30.0, -20.0, -10.0, -3.0, 0.0]
        assert _classify_behavior(gains, 1000.0) == "high-pass"

    def test_bandpass(self):
        gains = [-30.0, -20.0, 0.0, -20.0, -30.0]
        assert _classify_behavior(gains, 1000.0) == "band-pass"


# ---------------------------------------------------------------------------
# FACT_EXTRACTORS registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_all_topologies_have_extractor(self):
        expected = {
            "voltage_divider",
            "rc_lowpass",
            "rc_highpass",
            "rlc_bandpass",
            "half_wave_rectifier",
        }
        assert set(FACT_EXTRACTORS.keys()) == expected

    def test_extractors_are_callable(self):
        for name, extractor in FACT_EXTRACTORS.items():
            assert callable(extractor), f"{name} extractor is not callable"


# ---------------------------------------------------------------------------
# Voltage divider extractor
# ---------------------------------------------------------------------------


class TestVoltageDividerExtractor:
    def test_basic(self):
        parsed = {"V(out)": 3.0}
        params = {"Vin_dc": 9.0}
        facts = FACT_EXTRACTORS["voltage_divider"](parsed, params)
        assert facts["Vout_dc"] == 3.0
        assert facts["divider_ratio"] == pytest.approx(1.0 / 3.0)


# ---------------------------------------------------------------------------
# RC low-pass extractor
# ---------------------------------------------------------------------------


class TestRcLowPassExtractor:
    def test_basic(self):
        parsed = {
            "V(out)": [
                (1.0, 0.0),
                (100.0, -0.1),
                (1000.0, -3.0),
                (10000.0, -20.0),
            ],
        }
        facts = FACT_EXTRACTORS["rc_lowpass"](parsed, {})
        assert facts["behavior"] == "low-pass"
        assert facts["passband_gain_db"] == 0.0
        assert 500 < facts["cutoff_hz"] < 2000

    def test_empty_data(self):
        facts = FACT_EXTRACTORS["rc_lowpass"]({}, {})
        assert facts["cutoff_hz"] == 0.0
        assert facts["behavior"] == "none"


# ---------------------------------------------------------------------------
# RLC band-pass extractor
# ---------------------------------------------------------------------------


class TestRlcBandPassExtractor:
    def test_basic(self):
        parsed = {
            "V(out)": [
                (10.0, -30.0),
                (100.0, -20.0),
                (1000.0, 0.0),
                (10000.0, -20.0),
                (100000.0, -30.0),
            ],
        }
        facts = FACT_EXTRACTORS["rlc_bandpass"](parsed, {})
        assert 800 < facts["center_freq_hz"] < 1200
        assert facts["peak_gain_db"] == 0.0
        assert facts["Q"] > 0


# ---------------------------------------------------------------------------
# Half-wave rectifier extractor
# ---------------------------------------------------------------------------


class TestHalfWaveRectifierExtractor:
    def test_basic(self):
        # Steady-state rectified waveform
        data = [(0.01, 4.0), (0.02, 4.5), (0.03, 4.0), (0.04, 4.5)]
        parsed = {"V(out)": data}
        facts = FACT_EXTRACTORS["half_wave_rectifier"](parsed, {})
        assert facts["Vout_peak"] == 4.5
        assert 4.0 < facts["Vout_dc"] < 4.5
        assert facts["ripple_vpp"] == 0.5

    def test_empty_data(self):
        facts = FACT_EXTRACTORS["half_wave_rectifier"]({}, {})
        assert facts["Vout_peak"] == 0.0
        assert facts["Vout_dc"] == 0.0
        assert facts["ripple_vpp"] == 0.0
