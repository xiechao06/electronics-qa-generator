"""Tests for questions/templates.py — registry and content."""

from __future__ import annotations

from electronics_qa_generator.questions.templates import QUESTION_TEMPLATES


class TestRegistry:
    def test_all_topologies_present(self):
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
        }
        assert set(QUESTION_TEMPLATES.keys()) == expected

    def test_each_topology_has_at_least_two(self):
        for name, templates in QUESTION_TEMPLATES.items():
            assert len(templates) >= 2, f"{name} has fewer than 2 templates"

    def test_total_template_count(self):
        total = sum(len(t) for t in QUESTION_TEMPLATES.values())
        assert total == 63


class TestTemplateStructure:
    def test_required_keys(self):
        for name, templates in QUESTION_TEMPLATES.items():
            for tmpl in templates:
                assert "id" in tmpl, f"{name} template missing 'id'"
                assert "question_type" in tmpl
                assert "question_template" in tmpl
                assert "program" in tmpl
                assert "answer_keys" in tmpl

    def test_valid_question_types(self):
        valid_types = {"direct", "derived", "classification", "comparison"}
        for name, templates in QUESTION_TEMPLATES.items():
            for tmpl in templates:
                assert tmpl["question_type"] in valid_types, (
                    f"{name}/{tmpl['id']}: invalid type {tmpl['question_type']!r}"
                )

    def test_program_is_non_empty_list(self):
        for name, templates in QUESTION_TEMPLATES.items():
            for tmpl in templates:
                assert isinstance(tmpl["program"], list)
                assert len(tmpl["program"]) > 0, f"{name}/{tmpl['id']}: empty program"

    def test_ids_are_unique_within_topology(self):
        for name, templates in QUESTION_TEMPLATES.items():
            ids = [t["id"] for t in templates]
            assert len(ids) == len(set(ids)), f"{name}: duplicate ids"


class TestQuestionTypeCoverage:
    def test_direct_questions_exist(self):
        for name in QUESTION_TEMPLATES:
            direct = [t for t in QUESTION_TEMPLATES[name] if t["question_type"] == "direct"]
            assert len(direct) >= 1, f"{name}: no direct questions"

    def test_at_least_one_type_per_topology(self):
        all_types = {"direct", "derived", "classification", "comparison"}
        for name, templates in QUESTION_TEMPLATES.items():
            types_found = {t["question_type"] for t in templates}
            assert types_found & all_types, f"{name}: no question types found"
