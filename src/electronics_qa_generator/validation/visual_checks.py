"""Vision-model-assisted QA-item quality checks.

Two checks operating on rendered schematic PNGs:
- check_topology_match: VLM verifies the schematic matches the topology name
- check_label_visibility: VLM checks component labels are readable

Uses the vision provider (Ollama deepseek-vl2-tiny by default).
All checks are advisory (WARN, never FAIL); pass-through on unavailability.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Callable

from ..models import QAItem
from .models import CheckResult, Verdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class VisualCheckCache:
    """Disk-backed cache for visual check results, keyed by image hash."""

    def __init__(self, cache_dir: Path | str | None = None):
        if cache_dir is None:
            cache_dir = Path(".cache/eqa/visual_checks")
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, check_name: str, image_path: str) -> str:
        try:
            img_hash = hashlib.sha256(Path(image_path).read_bytes()).hexdigest()[:16]
        except Exception:
            img_hash = hashlib.sha256(image_path.encode()).hexdigest()[:16]
        return f"{check_name}|{img_hash}"

    def get(self, check_name: str, image_path: str) -> dict | None:
        filepath = self._cache_dir / f"{self._key(check_name, image_path)}.json"
        if not filepath.exists():
            return None
        try:
            return json.loads(filepath.read_text())  # type: ignore[no-any-return]
        except json.JSONDecodeError, OSError:
            return None

    def put(self, check_name: str, image_path: str, result: dict) -> None:
        filepath = self._cache_dir / f"{self._key(check_name, image_path)}.json"
        filepath.write_text(json.dumps(result, indent=2, default=str))


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_TOPOLOGY_SYSTEM = """\
You are an electronics schematic reviewer.

Analyze the provided circuit schematic image and determine if it matches
the stated topology.

Circuit symbol guide:
- Zigzag line = resistor (R)
- Two parallel vertical lines = capacitor (C)
- Coiled/looped line = inductor (L)
- Triangle pointing to a vertical bar = diode (D)
- Circle with + and - inside = voltage source (V)

Respond with exactly one of:

PASS — the schematic matches the stated topology
WARN: <reason> — if the schematic does not match the stated topology"""

_LABEL_SYSTEM = """\
You are a schematic image quality reviewer.

Examine the provided circuit schematic image and check whether all component
reference labels (like R1, C1, L1, D1, V1) and their values (like "4.7k Ω",
"100n F") are clearly visible and readable.

Check for:
- Labels clipped at image edges
- Labels overlapping each other
- Labels too small to read
- Labels missing entirely

Respond with exactly one of:

PASS — all labels are clearly readable
WARN: <reason> — if any labels have visibility issues"""


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def _run_vision_check(
    check_name: str,
    system_prompt: str,
    user_prompt: str,
    schematic_path: str | None,
    *,
    provider: Callable | None = None,
    cache: VisualCheckCache | None = None,
) -> CheckResult:
    """Shared runner for vision checks with caching and pass-through."""

    if not schematic_path or not Path(schematic_path).exists():
        return CheckResult(check_name, Verdict.PASS, "no schematic to check")

    # Cache lookup
    if cache is not None:
        cached = cache.get(check_name, schematic_path)
        if cached is not None:
            return CheckResult(
                check_name,
                Verdict(cached["verdict"]),
                cached.get("message", ""),
            )

    # Provider availability
    if provider is None:
        from ..llm.provider import complete_vision

        provider = complete_vision

    try:
        response = provider(system_prompt, user_prompt, schematic_path)
    except Exception as exc:
        logger.info("Vision check %s failed: %s", check_name, exc)
        return CheckResult(check_name, Verdict.PASS, f"provider error: {exc}")

    if not response:
        return CheckResult(check_name, Verdict.PASS, "VLM unavailable")

    response = response.strip()

    # Parse
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
            schematic_path,
            {"verdict": result.verdict.value, "message": result.message},
        )

    return result


def check_topology_match(
    item: QAItem,
    schematic_path: str | None,
    *,
    provider: Callable | None = None,
    cache: VisualCheckCache | None = None,
    topology: str = "",
) -> CheckResult:
    """Verify the schematic image matches the stated topology name."""
    topo = topology or getattr(item, "topology", "unknown")
    user_prompt = f"Does this schematic image show a '{topo}' circuit topology?"
    return _run_vision_check(
        "topology_match",
        _TOPOLOGY_SYSTEM,
        user_prompt,
        schematic_path,
        provider=provider,
        cache=cache,
    )


def check_label_visibility(
    item: QAItem,
    schematic_path: str | None,
    *,
    provider: Callable | None = None,
    cache: VisualCheckCache | None = None,
) -> CheckResult:
    """Check that component labels are readable in the schematic image."""
    return _run_vision_check(
        "label_visibility",
        _LABEL_SYSTEM,
        "Are all component labels and values clearly readable in this schematic?",
        schematic_path,
        provider=provider,
        cache=cache,
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

VISUAL_CHECKS = [
    check_topology_match,
    check_label_visibility,
]
