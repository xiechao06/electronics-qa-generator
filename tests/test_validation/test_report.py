"""Tests for validation/report.py."""

from __future__ import annotations

from electronics_qa_generator.models import QAItem
from electronics_qa_generator.validation.report import ValidationReport


def _make_item(**kwargs) -> QAItem:
    defaults = {
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


class TestValidationReport:
    def test_all_pass(self):
        item = _make_item()
        facts = {"cutoff_hz": 233.0}
        report = ValidationReport.from_items([item], facts, {})
        assert report.ok is True
        assert report.fail_count == 0

    def test_ok_false_on_fail(self):
        item = _make_item()
        facts = {"cutoff_hz": 999.0}
        report = ValidationReport.from_items([item], facts, {})
        assert report.ok is False
        assert report.fail_count > 0

    def test_to_dict(self):
        item = _make_item()
        facts = {"cutoff_hz": 233.0}
        report = ValidationReport.from_items([item], facts, {})
        d = report.to_dict()
        assert "ok" in d
        assert "stats" in d
        assert d["stats"]["total_checks"] > 0

    def test_empty_items(self):
        report = ValidationReport.from_items([], {}, {})
        assert report.ok is True
