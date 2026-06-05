"""Humanization cache: disk-backed storage of reworded questions.

Mirrors ``simulation/cache.py``. Keys are content-addressed hashes of
``(original_question_text, model_name, options_signature)`` so that the
same input produces the same output without an extra provider call.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _cache_key(original_question: str, model: str, options_signature: str) -> str:
    """Derive a safe filename key from the cache inputs."""
    seed = f"{original_question}|{model}|{options_signature}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


class HumanizationCache:
    """Disk-backed cache of LLM-humanized Q/A text."""

    def __init__(self, cache_dir: Path | str | None = None):
        if cache_dir is None:
            cache_dir = Path(".cache/eqa/humanize")
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API (mirrors FactCache)
    # ------------------------------------------------------------------

    def get(
        self,
        original_question: str,
        model: str = "",
        options_signature: str = "",
    ) -> dict[str, Any] | None:
        """Return cached humanization result dict, or None."""
        key = _cache_key(original_question, model, options_signature)
        filepath = self._cache_dir / f"{key}.json"
        if not filepath.exists():
            return None
        try:
            return json.loads(filepath.read_text())  # type: ignore[no-any-return]
        except json.JSONDecodeError, OSError:
            return None

    def put(
        self,
        original_question: str,
        result: dict[str, Any],
        model: str = "",
        options_signature: str = "",
    ) -> None:
        """Store the humanization result dict."""
        key = _cache_key(original_question, model, options_signature)
        filepath = self._cache_dir / f"{key}.json"
        filepath.write_text(json.dumps(result, indent=2, default=str))
