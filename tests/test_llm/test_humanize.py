"""Tests for llm/humanize.py."""

from __future__ import annotations

from electronics_qa_generator.llm.cache import HumanizationCache
from electronics_qa_generator.llm.humanize import (
    _answer_preserved,
    _parse_response,
    humanize_item,
)
from electronics_qa_generator.llm.provider import DeepSeekError
from electronics_qa_generator.models import QAItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_item(
    question: str = "What is the cutoff frequency?",
    answer: str = "15.9 kHz",
    answer_value: float = 15900.0,
    unit: str = "Hz",
) -> QAItem:
    return QAItem(
        question_type="direct",
        question=question,
        answer=answer,
        answer_value=answer_value,
        unit=unit,
        tolerance=0.5,
        program=[],
    )


def _fake_provider_success(system: str, user: str) -> str:
    """Fake provider that returns a nicely reworded question + explanation."""
    return (
        "<question>Determine the −3 dB cutoff frequency of this RC low-pass filter.</question>\n"
        "<explanation>The cutoff frequency is given by fc = 1/(2πRC). "
        "With the given component values, fc = 15.9 kHz.</explanation>"
    )


# ---------------------------------------------------------------------------
# parse_response
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_extracts_both_fields(self):
        q, e = _parse_response(
            "<question>reworded question</question>\n<explanation>some explanation</explanation>"
        )
        assert q == "reworded question"
        assert e == "some explanation"

    def test_question_only(self):
        q, e = _parse_response("<question>reworded Q</question>")
        assert q == "reworded Q"
        assert e is None

    def test_empty_explanation_returns_none(self):
        q, e = _parse_response("<question>reworded Q</question>\n<explanation>  </explanation>")
        assert q == "reworded Q"
        assert e is None

    def test_fallback_to_raw_text(self):
        q, e = _parse_response("just some unformatted text")
        assert q == "just some unformatted text"
        assert e is None


# ---------------------------------------------------------------------------
# answer_preserved
# ---------------------------------------------------------------------------


class TestAnswerPreserved:
    def test_numeric_answer_returns_true(self):
        assert _answer_preserved("what is the voltage?", "5 V", "V") is True

    def test_non_numeric_answer_returns_true(self):
        assert _answer_preserved("is it active?", "active", None) is True


# ---------------------------------------------------------------------------
# humanize_item
# ---------------------------------------------------------------------------


class TestHumanizeItem:
    def test_preserves_all_answer_fields(self):
        item = _make_item()
        result = humanize_item(item, provider=_fake_provider_success)

        assert result.question_type == item.question_type
        assert result.answer == item.answer
        assert result.answer_value == item.answer_value
        assert result.unit == item.unit
        assert result.tolerance == item.tolerance
        assert result.program == item.program
        assert result.choices == item.choices

    def test_rewords_question(self):
        item = _make_item()
        result = humanize_item(item, provider=_fake_provider_success)
        assert "−3 dB cutoff" in result.question
        assert result.question != item.question

    def test_explanation_attached_when_enabled(self):
        item = _make_item()
        result = humanize_item(item, provider=_fake_provider_success, explain=True)
        assert result.explanation is not None
        assert "15.9 kHz" in result.explanation

    def test_explanation_none_when_disabled(self):
        def _no_explain(system, user):
            return "<question>reworded</question>"

        item = _make_item()
        result = humanize_item(item, provider=_no_explain, explain=False)
        assert result.explanation is None

    def test_pass_through_when_provider_raises(self):
        item = _make_item()

        def _fail(*args, **kwargs):
            raise DeepSeekError("boom")

        result = humanize_item(item, provider=_fail)
        # Question should be unchanged
        assert result.question == item.question
        assert result.answer == item.answer
        assert result.answer_value == item.answer_value

    def test_pass_through_when_provider_unexpected_error(self):
        item = _make_item()

        def _fail(*args, **kwargs):
            raise RuntimeError("unexpected")

        result = humanize_item(item, provider=_fail)
        assert result.question == item.question
        assert result.answer == item.answer

    def test_cache_hit_avoids_provider_call(self, tmp_path):
        item = _make_item()
        cache = HumanizationCache(cache_dir=tmp_path)

        # Pre-populate the cache
        cache.put(
            item.question,
            {"question": "cached reworded", "explanation": "cached explanation"},
            model="test-model",
            options_signature="explain=1",
        )

        # A provider that would fail if called
        def _must_not_call(*args, **kwargs):
            raise AssertionError("provider should not be called on cache hit")

        result = humanize_item(
            item,
            provider=_must_not_call,
            cache=cache,
            explain=True,
            model="test-model",
        )
        assert result.question == "cached reworded"
        assert result.explanation == "cached explanation"

    def test_cache_miss_calls_provider(self, tmp_path):
        item = _make_item()
        cache = HumanizationCache(cache_dir=tmp_path)
        assert cache.get(item.question, model="test-model", options_signature="explain=1") is None

        result = humanize_item(
            item,
            provider=_fake_provider_success,
            cache=cache,
            explain=True,
            model="test-model",
        )
        assert "−3 dB" in result.question

        # Now it should be in the cache
        cached = cache.get(item.question, model="test-model", options_signature="explain=1")
        assert cached is not None
