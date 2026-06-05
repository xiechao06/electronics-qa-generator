"""Tests for validation/visual_checks.py — VLM-assisted visual checks."""

from __future__ import annotations

from electronics_qa_generator.models import QAItem
from electronics_qa_generator.validation.models import Verdict
from electronics_qa_generator.validation.visual_checks import (
    VisualCheckCache,
    check_label_visibility,
    check_topology_match,
)


def _make_item(**kwargs) -> QAItem:
    defaults = {
        "question_type": "direct",
        "question": "Find the cutoff frequency.",
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


def _fake_vision_pass(system: str, user: str, image: str) -> str:
    return "PASS"


def _fake_vision_warn(system: str, user: str, image: str) -> str:
    return "WARN: topology mismatch detected"


class TestTopologyMatch:
    def test_pass(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")
        item = _make_item()
        r = check_topology_match(
            item,
            str(img),
            provider=_fake_vision_pass,
            topology="rc_lowpass",
        )
        assert r.verdict == Verdict.PASS

    def test_warn(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")
        item = _make_item()
        r = check_topology_match(
            item,
            str(img),
            provider=_fake_vision_warn,
            topology="rc_lowpass",
        )
        assert r.verdict == Verdict.WARN

    def test_no_schematic_passes(self):
        item = _make_item()
        r = check_topology_match(item, None, provider=_fake_vision_pass)
        assert r.verdict == Verdict.PASS


class TestLabelVisibility:
    def test_pass(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")
        item = _make_item()
        r = check_label_visibility(item, str(img), provider=_fake_vision_pass)
        assert r.verdict == Verdict.PASS

    def test_warn(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")
        item = _make_item()
        r = check_label_visibility(item, str(img), provider=_fake_vision_warn)
        assert r.verdict == Verdict.WARN

    def test_no_schematic_passes(self):
        item = _make_item()
        r = check_label_visibility(item, None, provider=_fake_vision_pass)
        assert r.verdict == Verdict.PASS


class TestVisualCheckCache:
    def test_put_get(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")
        cache = VisualCheckCache(cache_dir=tmp_path)
        cache.put("topology_match", str(img), {"verdict": "pass"})
        result = cache.get("topology_match", str(img))
        assert result is not None
        assert result["verdict"] == "pass"


class TestVisualFlagInHelp:
    def test_validate_visual_in_help(self):
        import sys
        from io import StringIO

        from electronics_qa_generator.cli import build_parser

        parser = build_parser()
        old = sys.stdout
        try:
            sys.stdout = StringIO()
            try:
                parser.parse_args(["validate", "--help"])
            except SystemExit:
                pass
            text = sys.stdout.getvalue()
        finally:
            sys.stdout = old
        assert "--visual" in text
