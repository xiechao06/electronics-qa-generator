"""Tests for validation/llm_checks.py — LLM-assisted verification checks."""

from __future__ import annotations


from electronics_qa_generator.models import QAItem
from electronics_qa_generator.validation.llm_checks import (
    LLMCheckCache,
    check_ambiguity,
    check_difficulty,
    check_semantic_leakage,
)
from electronics_qa_generator.validation.models import Verdict


def _make_item(**kwargs) -> QAItem:
    defaults = {
        "question_type": "direct",
        "question": "Find the cutoff frequency of this RC low-pass filter.",
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


def _fake_provider_pass(system: str, user: str) -> str:
    return "PASS"


def _fake_provider_warn(system: str, user: str) -> str:
    return "WARN: some issue detected"


def _fake_provider_easy(system: str, user: str) -> str:
    return "easy"


# ---------------------------------------------------------------------------
# Ambiguity
# ---------------------------------------------------------------------------


class TestCheckAmbiguity:
    def test_pass(self):
        item = _make_item()
        r = check_ambiguity(item, provider=_fake_provider_pass)
        assert r.verdict == Verdict.PASS

    def test_warn(self):
        item = _make_item()
        r = check_ambiguity(item, provider=_fake_provider_warn)
        assert r.verdict == Verdict.WARN

    def test_pass_when_no_provider(self):
        item = _make_item()
        r = check_ambiguity(item)  # no provider, is_available() likely False
        assert r.verdict == Verdict.PASS


# ---------------------------------------------------------------------------
# Semantic leakage
# ---------------------------------------------------------------------------


class TestCheckSemanticLeakage:
    def test_pass(self):
        item = _make_item()
        r = check_semantic_leakage(item, provider=_fake_provider_pass)
        assert r.verdict == Verdict.PASS

    def test_warn(self):
        item = _make_item()
        r = check_semantic_leakage(item, provider=_fake_provider_warn)
        assert r.verdict == Verdict.WARN


# ---------------------------------------------------------------------------
# Difficulty
# ---------------------------------------------------------------------------


class TestCheckDifficulty:
    def test_always_pass(self):
        item = _make_item()
        r = check_difficulty(item, provider=_fake_provider_easy)
        assert r.verdict == Verdict.PASS
        assert "easy" in r.message

    def test_no_provider_passes(self):
        item = _make_item()
        r = check_difficulty(item)
        assert r.verdict == Verdict.PASS


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class TestLLMCheckCache:
    def test_put_and_get(self, tmp_path):
        cache = LLMCheckCache(cache_dir=tmp_path)
        cache.put("ambiguity", "test question", {"verdict": "pass", "message": ""})
        result = cache.get("ambiguity", "test question")
        assert result is not None
        assert result["verdict"] == "pass"

    def test_miss(self, tmp_path):
        cache = LLMCheckCache(cache_dir=tmp_path)
        assert cache.get("ambiguity", "nonexistent") is None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestLLMFlagInHelp:
    def test_validate_llm_in_help(self):
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
        assert "--llm" in text
