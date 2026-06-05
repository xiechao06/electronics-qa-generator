"""Tests for questions/generator.py — QAItem generation."""

from __future__ import annotations

import pytest

from electronics_qa_generator.questions.generator import generate_questions


FACTS = {
    "Vout_dc": 3.0,
    "Vin_dc": 9.0,
    "cutoff_hz": 1590.0,
    "center_freq_hz": 10000.0,
    "bandwidth_hz": 2000.0,
    "Q": 5.0,
    "behavior": "low-pass",
    "passband_gain_db": -0.1,
    "peak_gain_db": 0.0,
    "Vout_peak": 4.5,
    "ripple_vpp": 0.5,
}


class TestGenerateQuestions:
    def test_voltage_divider_count(self):
        items = generate_questions("voltage_divider", FACTS, {})
        assert len(items) == 5

    def test_all_fields_populated(self):
        items = generate_questions("voltage_divider", FACTS, {})
        for item in items:
            assert item.question_type in {"direct", "derived", "classification", "comparison"}
            assert item.question
            assert item.answer
            assert isinstance(item.program, list)

    def test_choices_for_classification(self):
        items = generate_questions("rc_lowpass", FACTS, {})
        class_items = [i for i in items if i.question_type == "classification"]
        assert len(class_items) >= 1
        for item in class_items:
            assert item.choices is not None
            assert len(item.choices) >= 2

    def test_no_choices_for_direct(self):
        items = generate_questions("voltage_divider", FACTS, {})
        direct_items = [i for i in items if i.question_type == "direct"]
        for item in direct_items:
            assert item.choices is None

    def test_direct_has_answer_value(self):
        items = generate_questions("rc_lowpass", FACTS, {})
        direct = [i for i in items if i.question_type == "direct"]
        for item in direct:
            assert item.answer_value is not None

    def test_classification_has_no_answer_value(self):
        items = generate_questions("rc_lowpass", FACTS, {})
        class_items = [i for i in items if i.question_type == "classification"]
        for item in class_items:
            assert item.answer_value is None
            assert item.unit is None

    def test_unknown_topology_raises_keyerror(self):
        with pytest.raises(KeyError):
            generate_questions("nonexistent", FACTS, {})


class TestAllTopologies:
    def test_each_topology_generates(self):
        for topo in [
            "voltage_divider",
            "rc_lowpass",
            "rc_highpass",
            "rlc_bandpass",
            "half_wave_rectifier",
        ]:
            items = generate_questions(topo, FACTS, {})
            assert len(items) >= 2, f"{topo}: only {len(items)} items"

    def test_all_item_ids_are_unique(self):
        """No two generated questions have the same question text + type."""
        for topo in [
            "voltage_divider",
            "rc_lowpass",
        ]:
            items = generate_questions(topo, FACTS, {})
            keys = [(i.question_type, i.question) for i in items]
            assert len(keys) == len(set(keys)), f"{topo}: duplicate questions"
