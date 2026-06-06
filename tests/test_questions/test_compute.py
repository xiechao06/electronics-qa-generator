"""Tests for questions/compute.py — answer computation."""

from __future__ import annotations

from electronics_qa_generator.questions.compute import compute_answer
from electronics_qa_generator.questions import programs as P


class TestDirectNumeric:
    def test_vout_dc(self):
        program = [
            P.read_fact("Vout_dc"),
            P.format_numeric("$0", unit="V", precision=3),
        ]
        value, text, unit, tol = compute_answer(
            program,
            {"Vout_dc": 3.14},
            {},
        )
        assert value == 3.14
        assert "3.14" in text
        assert unit == "V"
        assert tol == 0.0005

    def test_cutoff_hz(self):
        program = [
            P.read_fact("cutoff_hz"),
            P.format_numeric("$0", unit="Hz", precision=3),
        ]
        value, text, unit, tol = compute_answer(
            program,
            {"cutoff_hz": 1590.0},
            {},
        )
        assert value == 1590.0
        assert unit == "Hz"


class TestDerived:
    def test_divider_ratio(self):
        program = [
            P.read_fact("Vout_dc"),
            P.read_fact("Vin_dc"),
            P.div("$0", "$1"),
            P.format_numeric("$2", unit=None, precision=4),
        ]
        value, text, unit, tol = compute_answer(
            program,
            {"Vout_dc": 3.0, "Vin_dc": 9.0},
            {},
        )
        assert value == round(3.0 / 9.0, 4)  # rounded to precision 4
        assert unit is None
        assert tol == 5e-05

    def test_q_factor(self):
        program = [
            P.read_fact("center_freq_hz"),
            P.read_fact("bandwidth_hz"),
            P.div("$0", "$1"),
            P.format_numeric("$2", unit=None, precision=3),
        ]
        value, text, unit, tol = compute_answer(
            program,
            {"center_freq_hz": 1000.0, "bandwidth_hz": 200.0},
            {},
        )
        assert value == 5.0


class TestClassification:
    def test_behavior_lowpass(self):
        program = [
            P.read_fact("behavior"),
            P.classify("$0", ["low-pass", "high-pass", "band-pass"]),
            P.return_label("$1"),
        ]
        value, text, unit, tol = compute_answer(
            program,
            {"behavior": "low-pass"},
            {},
        )
        assert value is None
        assert text == "low-pass"
        assert unit is None
        assert tol is None

    def test_behavior_unknown_gets_last_label(self):
        program = [
            P.read_fact("behavior"),
            P.classify("$0", ["low-pass", "high-pass"]),
            P.return_label("$1"),
        ]
        value, text, unit, tol = compute_answer(
            program,
            {"behavior": "notch"},
            {},
        )
        assert text == "high-pass"


class TestComparison:
    def test_cutoff_above_1khz_true(self):
        program = [
            P.read_fact("cutoff_hz"),
            P.push_const(1000.0),
            P.compare(">"),
            P.return_bool("$2", true_label="above", false_label="below"),
        ]
        value, text, unit, tol = compute_answer(
            program,
            {"cutoff_hz": 5000.0},
            {},
        )
        assert value is None
        assert text == "above"
        assert unit is None
        assert tol is None

    def test_cutoff_below_1khz(self):
        program = [
            P.read_fact("cutoff_hz"),
            P.push_const(1000.0),
            P.compare(">"),
            P.return_bool("$2", true_label="above", false_label="below"),
        ]
        value, text, unit, tol = compute_answer(
            program,
            {"cutoff_hz": 100.0},
            {},
        )
        assert text == "below"


class TestEdgeCases:
    def test_empty_program(self):
        value, text, unit, tol = compute_answer([], {}, {})
        assert value is None
        assert text == ""

    def test_missing_fact_defaults_to_zero(self):
        program = [
            P.read_fact("nonexistent"),
            P.format_numeric("$0", unit="V", precision=2),
        ]
        value, text, unit, tol = compute_answer(program, {}, {})
        assert value == 0.0
