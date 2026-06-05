"""Tests for llm/cache.py."""

from __future__ import annotations

from electronics_qa_generator.llm.cache import HumanizationCache


class TestHumanizationCache:
    def test_put_and_get_roundtrip(self, tmp_path):
        cache = HumanizationCache(cache_dir=tmp_path)
        cache.put(
            "original question text",
            {"question": "reworded", "explanation": "some explanation"},
            model="deepseek-v4-pro",
            options_signature="explain=1",
        )

        result = cache.get(
            "original question text",
            model="deepseek-v4-pro",
            options_signature="explain=1",
        )
        assert result is not None
        assert result["question"] == "reworded"
        assert result["explanation"] == "some explanation"

    def test_miss_returns_none(self, tmp_path):
        cache = HumanizationCache(cache_dir=tmp_path)
        assert cache.get("never cached") is None

    def test_key_sensitive_to_model(self, tmp_path):
        cache = HumanizationCache(cache_dir=tmp_path)
        cache.put(
            "question",
            {"question": "v4-pro output"},
            model="deepseek-v4-pro",
        )
        # Different model => different key => cache miss
        assert cache.get("question", model="other-model") is None

    def test_key_sensitive_to_options(self, tmp_path):
        cache = HumanizationCache(cache_dir=tmp_path)
        cache.put(
            "question",
            {"question": "with explain"},
            options_signature="explain=1",
        )
        assert cache.get("question", options_signature="explain=0") is None

    def test_key_sensitive_to_question_text(self, tmp_path):
        cache = HumanizationCache(cache_dir=tmp_path)
        cache.put("question A", {"question": "reworded A"})
        assert cache.get("question B") is None

    def test_corrupted_file_returns_none(self, tmp_path):
        cache = HumanizationCache(cache_dir=tmp_path)
        # Write a corrupted file at the expected key path manually
        import hashlib

        key = hashlib.sha256("corrupt|deepseek-v4-pro|".encode()).hexdigest()[:16]
        (tmp_path / f"{key}.json").write_text("not valid json")
        result = cache.get("corrupt", model="deepseek-v4-pro")
        assert result is None
