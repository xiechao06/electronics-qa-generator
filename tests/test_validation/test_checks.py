"""Tests for validation/checks.py — all 7 static verification checks."""

from __future__ import annotations


from electronics_qa_generator.models import QAItem
from electronics_qa_generator.validation.checks import (
    check_answer,
    check_coverage,
    check_degenerate,
    check_leakage,
    check_params,
    check_tolerance,
    check_unit,
)
from electronics_qa_generator.validation.models import Verdict


def _make_item(**kwargs) -> QAItem:
    defaults: dict = {
        "question_type": "direct",
        "question": "What is the cutoff frequency?",
        "answer": "233 Hz",
        "answer_value": 233.0,
        "unit": "Hz",
        "tolerance": 0.5,
        "program": [
            {"op": "read_fact", "fact": "cutoff_hz"},
            {"op": "format_numeric", "value": "$0", "unit": "Hz", "precision": 0},
        ],
    }
    defaults.update(kwargs)
    return QAItem(**defaults)


# ---------------------------------------------------------------------------
# Check 1: Answer
# ---------------------------------------------------------------------------


class TestCheckAnswer:
    def test_pass(self):
        facts = {"cutoff_hz": 233.0}
        item = _make_item()
        r = check_answer(item, facts)
        assert r.verdict == Verdict.PASS

    def test_fail_wrong_value(self):
        facts = {"cutoff_hz": 999.0}
        item = _make_item()
        r = check_answer(item, facts)
        assert r.verdict == Verdict.FAIL


# ---------------------------------------------------------------------------
# Check 2: Parameters
# ---------------------------------------------------------------------------


class TestCheckParams:
    def test_pass(self):
        item = _make_item(
            question="Given R = 4.7k Ω, C = 100n F, find fc.",
        )
        params = {"R1_ohm": 4700.0, "C1_f": 1e-7}
        r = check_params(item, params)
        assert r.verdict == Verdict.PASS

    def test_fail_wrong_value(self):
        item = _make_item(
            question="Given R = 4.7k Ω, C = 100n F, find fc.",
        )
        params = {"R1_ohm": 10000.0, "C1_f": 1e-7}
        r = check_params(item, params)
        assert r.verdict == Verdict.FAIL

    def test_no_params(self):
        item = _make_item(question="What is Vout?")
        r = check_params(item, {})
        assert r.verdict == Verdict.PASS


# ---------------------------------------------------------------------------
# Check 3: Unit
# ---------------------------------------------------------------------------


class TestCheckUnit:
    def test_pass(self):
        item = _make_item(question="Find the cutoff in Hz.", unit="Hz")
        r = check_unit(item)
        assert r.verdict == Verdict.PASS

    def test_fail_khz_vs_hz(self):
        item = _make_item(
            question="Find the cutoff in kHz.",
            unit="Hz",
        )
        r = check_unit(item)
        assert r.verdict == Verdict.FAIL

    def test_no_unit(self):
        item = _make_item(unit=None)
        r = check_unit(item)
        assert r.verdict == Verdict.PASS


# ---------------------------------------------------------------------------
# Check 4: Leakage
# ---------------------------------------------------------------------------


class TestCheckLeakage:
    def test_pass(self):
        item = _make_item(answer="233 Hz")
        r = check_leakage(item)
        assert r.verdict == Verdict.PASS

    def test_warn(self):
        item = _make_item(
            question="The answer 233 Hz is correct.",
            answer="233 Hz",
        )
        r = check_leakage(item)
        assert r.verdict == Verdict.WARN

    def test_classification_skipped(self):
        item = _make_item(
            question_type="classification",
            question="Is this low-pass, high-pass, or band-pass?",
            answer="low-pass",
        )
        r = check_leakage(item)
        assert r.verdict == Verdict.PASS


# ---------------------------------------------------------------------------
# Check 5: Degenerate
# ---------------------------------------------------------------------------


class TestCheckDegenerate:
    def test_pass(self):
        item = _make_item(answer_value=233.0, unit="Hz")
        r = check_degenerate(item)
        assert r.verdict == Verdict.PASS

    def test_nan(self):
        item = _make_item(answer_value=float("nan"))
        r = check_degenerate(item)
        assert r.verdict == Verdict.FAIL

    def test_inf(self):
        item = _make_item(answer_value=float("inf"))
        r = check_degenerate(item)
        assert r.verdict == Verdict.FAIL

    def test_zero_frequency(self):
        item = _make_item(answer_value=0.0, unit="Hz")
        r = check_degenerate(item)
        assert r.verdict == Verdict.FAIL

    def test_none_value(self):
        item = _make_item(answer_value=None)
        r = check_degenerate(item)
        assert r.verdict == Verdict.PASS

    def test_extreme_gain(self):
        item = _make_item(answer_value=-500.0, unit="dB")
        r = check_degenerate(item)
        assert r.verdict == Verdict.FAIL


# ---------------------------------------------------------------------------
# Check 6: Tolerance
# ---------------------------------------------------------------------------


class TestCheckTolerance:
    def test_pass(self):
        item = _make_item(answer_value=233.0, tolerance=0.5)
        r = check_tolerance(item)
        assert r.verdict == Verdict.PASS

    def test_fail_large_relative(self):
        item = _make_item(answer_value=100.0, tolerance=80.0)
        r = check_tolerance(item)
        assert r.verdict == Verdict.FAIL

    def test_pass_near_zero_absolute(self):
        item = _make_item(answer_value=-9e-9, tolerance=0.005)
        r = check_tolerance(item)
        assert r.verdict == Verdict.PASS

    def test_warn_tight_tolerance(self):
        item = _make_item(answer_value=1.0, tolerance=1e-15)
        r = check_tolerance(item)
        assert r.verdict == Verdict.WARN


# ---------------------------------------------------------------------------
# Check 7: Coverage
# ---------------------------------------------------------------------------


class TestCheckCoverage:
    def test_good_coverage(self):
        items = [
            _make_item(question_type="direct", question="What is fc?"),
            _make_item(question_type="classification", question="Classify this."),
            _make_item(question_type="comparison", question="Is fc > 1 kHz?"),
        ]
        r = check_coverage(items)
        assert r.verdict == Verdict.PASS

    def test_single_type(self):
        items = [
            _make_item(question_type="direct"),
            _make_item(question_type="direct"),
        ]
        r = check_coverage(items)
        assert r.verdict == Verdict.WARN

    def test_single_item(self):
        r = check_coverage([_make_item()])
        assert r.verdict == Verdict.PASS
