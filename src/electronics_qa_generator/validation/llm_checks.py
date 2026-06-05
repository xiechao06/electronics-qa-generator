"""LLM-assisted QA-item quality checks.

Three checks using the DeepSeek provider:
- check_ambiguity: detects vague/ambiguous phrasing
- check_semantic_leakage: detects implicit answer leakage
- check_difficulty: scores difficulty (easy/medium/hard)

All checks are advisory (WARN, never FAIL) and best-effort (PASS on
provider unavailability). Results are cached by question text.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Callable

from ..llm.provider import DeepSeekError, is_available, complete as provider_complete
from ..models import QAItem
from .models import CheckResult, Verdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class LLMCheckCache:
    """Disk-backed cache for LLM check results, keyed by (check_name, question)."""

    def __init__(self, cache_dir: Path | str | None = None):
        if cache_dir is None:
            cache_dir = Path(".cache/eqa/llm_checks")
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, check_name: str, question: str) -> str:
        seed = f"{check_name}|{question}"
        return hashlib.sha256(seed.encode()).hexdigest()[:16]

    def get(self, check_name: str, question: str) -> dict | None:
        filepath = self._cache_dir / f"{self._key(check_name, question)}.json"
        if not filepath.exists():
            return None
        try:
            return json.loads(filepath.read_text())  # type: ignore[no-any-return]
        except json.JSONDecodeError, OSError:
            return None

    def put(self, check_name: str, question: str, result: dict) -> None:
        filepath = self._cache_dir / f"{self._key(check_name, question)}.json"
        filepath.write_text(json.dumps(result, indent=2, default=str))


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_AMBIGUITY_SYSTEM = """\
You are a quality reviewer for electronics exam questions.

Your task: determine if the question contains ambiguous or vague phrasing
that could confuse a student.

Guidelines:
- "the output" without specifying which node → ambiguous
- "the filter" when multiple filters exist → ambiguous
- "reasonable value" without bounds → vague
- Well-defined quantities with explicit nodes → clear

Respond with exactly one of:

PASS
or
WARN: <brief reason>"""

_LEAKAGE_SYSTEM = """\
You are a quality reviewer for electronics exam questions.

Your task: determine if the question IMPLICITLY reveals its own answer
through phrasing. This is NOT about the answer appearing as a label in
multiple-choice options — it's about the answer being embedded in the
question's premise.

Example leakage: "Given the cutoff frequency is 233 Hz, find the bandwidth."
→ The answer (233 Hz) is stated in the question.

Not leakage: "Is this a low-pass or high-pass filter?" (labels are options)

Respond with exactly one of:

PASS
or
WARN: <brief reason>"""

_DIFFICULTY_SYSTEM = """\
You are an electronics curriculum designer rating exam question difficulty.

Your task: rate this question's cognitive complexity as one of:
- easy: simple recall of a directly measured or computed value
- medium: requires applying a formula or comparing two values
- hard: requires multi-step derivation, unit conversion, or conceptual reasoning

Respond with exactly one word: easy, medium, or hard."""


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def _run_llm_check(
    item: QAItem,
    check_name: str,
    system_prompt: str,
    user_message: str,
    *,
    provider: Callable[..., str] | None = None,
    cache: LLMCheckCache | None = None,
) -> CheckResult:
    """Shared runner for all LLM checks with caching and pass-through."""

    # Cache lookup
    if cache is not None:
        cached = cache.get(check_name, item.question)
        if cached is not None:
            return CheckResult(
                check_name,
                Verdict(cached["verdict"]),
                cached.get("message", ""),
            )

    # Provider availability
    if provider is None and not is_available():
        return CheckResult(check_name, Verdict.PASS, "LLM not available")

    used_provider = provider if provider is not None else provider_complete

    try:
        response = used_provider(system_prompt, user_message)
    except (DeepSeekError, Exception) as exc:
        logger.info("LLM check %s failed: %s", check_name, exc)
        return CheckResult(check_name, Verdict.PASS, f"provider error: {exc}")

    response = response.strip()

    # Parse verdict
    verdict = Verdict.PASS
    message = response
    if response.upper().startswith("WARN"):
        verdict = Verdict.WARN
        if ":" in response:
            message = response.split(":", 1)[1].strip()

    result = CheckResult(check_name, verdict, message)

    # Store in cache
    if cache is not None:
        cache.put(
            check_name,
            item.question,
            {"verdict": result.verdict.value, "message": result.message},
        )

    return result


def check_ambiguity(
    item: QAItem,
    *,
    provider: Callable[..., str] | None = None,
    cache: LLMCheckCache | None = None,
) -> CheckResult:
    """Check for ambiguous or vague question wording."""
    return _run_llm_check(
        item,
        "ambiguity",
        _AMBIGUITY_SYSTEM,
        item.question,
        provider=provider,
        cache=cache,
    )


def check_semantic_leakage(
    item: QAItem,
    *,
    provider: Callable[..., str] | None = None,
    cache: LLMCheckCache | None = None,
) -> CheckResult:
    """Check for implicit answer leakage in question text."""
    user_msg = f"Question: {item.question}\n\nAnswer: {item.answer}"
    return _run_llm_check(
        item,
        "leakage_llm",
        _LEAKAGE_SYSTEM,
        user_msg,
        provider=provider,
        cache=cache,
    )


def check_difficulty(
    item: QAItem,
    *,
    provider: Callable[..., str] | None = None,
    cache: LLMCheckCache | None = None,
) -> CheckResult:
    """Score question difficulty as easy/medium/hard (always PASS)."""
    return _run_llm_check(
        item,
        "difficulty",
        _DIFFICULTY_SYSTEM,
        item.question,
        provider=provider,
        cache=cache,
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

LLM_CHECKS = [
    check_ambiguity,
    check_semantic_leakage,
    check_difficulty,
]
