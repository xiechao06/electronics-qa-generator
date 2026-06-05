"""Static verification checks for QA items.

Each check is a pure function: ``(QAItem, facts, params) -> CheckResult``.
None of them requires I/O or an LLM.
"""

from __future__ import annotations

import math
import re
from typing import Any

from ..models import QAItem
from ..questions.compute import compute_answer
from .models import CheckResult, Verdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_numeric(text: str) -> list[float]:
    """Return all numeric values found in *text*."""
    return [float(m) for m in re.findall(r"[-+]?\d+(?:\.\d+)?", text)]


def _has_unit_mismatch(question_text: str, answer_unit: str | None) -> bool:
    """Check if the question mentions a unit that conflicts with the answer."""
    if not answer_unit:
        return False
    # Normalize: lowercase, strip spaces
    q = question_text.lower()
    au = answer_unit.lower().strip()
    # Known conflicting units
    conflicts: dict[str, str] = {
        "hz": "khz",
        "khz": "hz",
        "v": "mv",
        "mv": "v",
        "a": "ma",
        "ma": "a",
        "db": "dbm",
        "w": "mw",
        "mw": "w",
        "s": "ms",
        "ms": "s",
    }
    conflict = conflicts.get(au)
    if conflict and conflict in q:
        return True
    return False


# ---------------------------------------------------------------------------
# Check 1: Answer recomputation
# ---------------------------------------------------------------------------


def check_answer(item: QAItem, facts: dict[str, Any]) -> CheckResult:
    """Recompute the answer from facts using the stored program.

    Returns PASS if all answer fields match byte-for-byte.
    """
    if not item.program:
        return CheckResult("answer", Verdict.PASS, "no program to verify")

    result = compute_answer(item.program, facts, {})
    if result is None:
        return CheckResult("answer", Verdict.FAIL, "compute_answer returned None")

    rec_value, rec_text, rec_unit, rec_tolerance = result

    failures: list[str] = []
    if rec_text != item.answer:
        failures.append(f"answer: '{rec_text}' != '{item.answer}'")
    if rec_value != item.answer_value:
        failures.append(f"value: {rec_value} != {item.answer_value}")
    if rec_unit != item.unit:
        failures.append(f"unit: '{rec_unit}' != '{item.unit}'")
    if rec_tolerance != item.tolerance:
        failures.append(f"tolerance: {rec_tolerance} != {item.tolerance}")

    if failures:
        return CheckResult("answer", Verdict.FAIL, "; ".join(failures))
    return CheckResult("answer", Verdict.PASS, "")


# ---------------------------------------------------------------------------
# Check 2: Parameter consistency
# ---------------------------------------------------------------------------


def check_params(item: QAItem, params: dict[str, Any]) -> CheckResult:
    """Verify component values in question text match sampled parameters.

    For each parameter key (e.g., R1_ohm), format the value (with unit) and
    check that the formatted string appears in the question text.
    """
    if not params:
        return CheckResult("params", Verdict.PASS, "no parameters to check")

    from ..graph.spice_emitter import (
        _fmt_capacitance,
        _fmt_inductance,
        _fmt_resistance,
        _fmt_voltage,
    )

    suffix_map: dict[str, tuple[str, Any]] = {
        "_ohm": ("Ω", _fmt_resistance),
        "_f": ("F", _fmt_capacitance),
        "_h": ("H", _fmt_inductance),
        "_volt": ("V", _fmt_voltage),
        "_v": ("V", _fmt_voltage),
        "_dc": ("V", _fmt_voltage),
        "_amplitude": ("V", _fmt_voltage),
    }

    missing: list[str] = []
    for key, raw_val in params.items():
        if not isinstance(raw_val, (int, float)):
            continue
        for suffix, (unit_symbol, fmt_fn) in suffix_map.items():
            if key.endswith(suffix):
                formatted = fmt_fn(raw_val)
                # Clean trailing .0 for integer values
                cleaned = re.sub(r"\.0+(?=\D|$)", "", formatted)
                search = f"{cleaned} {unit_symbol}"
                # Also check compact form (no space)
                compact = f"{cleaned}{unit_symbol}"
                if search not in item.question and compact not in item.question:
                    missing.append(f"{key}={raw_val} → '{search}' not in question")
                break

    if missing:
        return CheckResult(
            "params",
            Verdict.FAIL,
            "; ".join(missing),
        )
    return CheckResult("params", Verdict.PASS, "")


# ---------------------------------------------------------------------------
# Check 3: Unit consistency
# ---------------------------------------------------------------------------


def check_unit(item: QAItem) -> CheckResult:
    """Detect unit mismatches between question text and answer."""
    if not item.unit:
        return CheckResult("unit", Verdict.PASS, "no unit to check")
    if _has_unit_mismatch(item.question, item.unit):
        return CheckResult(
            "unit",
            Verdict.FAIL,
            f"question mentions conflicting unit vs answer '{item.unit}'",
        )
    return CheckResult("unit", Verdict.PASS, "")


# ---------------------------------------------------------------------------
# Check 4: Literal answer leakage
# ---------------------------------------------------------------------------


def check_leakage(item: QAItem) -> CheckResult:
    """Detect when the answer string appears verbatim in the question."""
    if not item.answer or len(item.answer) <= 2:
        return CheckResult("leakage", Verdict.PASS, "no answer to leak")

    # Skip classification labels — they're expected in the question
    if item.question_type == "classification":
        return CheckResult("leakage", Verdict.PASS, "classification — labels expected")

    # Check for the answer as a whole word/phrase
    ans_lower = item.answer.lower().strip()
    q_lower = item.question.lower()
    if ans_lower in q_lower:
        return CheckResult(
            "leakage",
            Verdict.WARN,
            f"answer '{item.answer}' appears in question",
        )

    return CheckResult("leakage", Verdict.PASS, "")


# ---------------------------------------------------------------------------
# Check 5: Degenerate values
# ---------------------------------------------------------------------------


def check_degenerate(item: QAItem) -> CheckResult:
    """Flag NaN, inf, or implausible values for their unit."""
    av = item.answer_value
    if av is None:
        return CheckResult("degenerate", Verdict.PASS, "no numeric value")

    if math.isnan(av):
        return CheckResult("degenerate", Verdict.FAIL, "answer_value is NaN")
    if math.isinf(av):
        return CheckResult("degenerate", Verdict.FAIL, "answer_value is ±inf")

    unit = (item.unit or "").lower().strip()
    # Unit-dependent plausibility bounds
    if unit in ("hz", "khz", "mhz"):
        if av <= 0.0:
            return CheckResult("degenerate", Verdict.FAIL, f"frequency {av} ≤ 0")
        if av > 1e12:
            return CheckResult("degenerate", Verdict.WARN, f"frequency {av} implausibly high")
    if unit in ("v", "mv", "kv"):
        if abs(av) > 1e6:
            return CheckResult("degenerate", Verdict.WARN, f"voltage magnitude {av} implausible")
    if unit == "db":
        if av < -300:
            return CheckResult("degenerate", Verdict.FAIL, f"gain {av} dB implausible")

    return CheckResult("degenerate", Verdict.PASS, "")


# ---------------------------------------------------------------------------
# Check 6: Tolerance appropriateness
# ---------------------------------------------------------------------------


def check_tolerance(item: QAItem) -> CheckResult:
    """Verify tolerance is reasonable relative to the answer magnitude."""
    av = item.answer_value
    tol = item.tolerance
    if av is None or tol is None:
        return CheckResult("tolerance", Verdict.PASS, "no numeric value")

    if tol <= 1e-12:
        return CheckResult("tolerance", Verdict.WARN, f"suspiciously tight tolerance {tol}")

    abs_av = abs(av)
    if abs_av < 1e-6:
        # Near-zero: use absolute tolerance check
        if tol > 0.01:
            return CheckResult(
                "tolerance",
                Verdict.WARN,
                f"large absolute tolerance {tol} for near-zero value {av}",
            )
        return CheckResult("tolerance", Verdict.PASS, "absolute tolerance acceptable")

    rel = tol / abs_av
    if rel > 0.5:
        return CheckResult(
            "tolerance",
            Verdict.FAIL,
            f"relative tolerance {rel:.1%} exceeds 50% (tol={tol}, val={av})",
        )
    return CheckResult("tolerance", Verdict.PASS, "")


# ---------------------------------------------------------------------------
# Check 7: Template coverage
# ---------------------------------------------------------------------------


def check_coverage(items: list[QAItem]) -> CheckResult:
    """Check question type diversity and duplicate detection for a batch.

    This check operates on a list of items from one topology, not a single item.
    """
    if len(items) < 2:
        return CheckResult("coverage", Verdict.PASS, "single item, no coverage check")

    types = {it.question_type for it in items}
    if len(types) < 2:
        return CheckResult(
            "coverage",
            Verdict.WARN,
            f"only {len(types)} question type(s) across {len(items)} items",
        )

    # Check no identical question texts across items (exact duplicate detection)
    seen_texts: set[str] = set()
    for it in items:
        if it.question in seen_texts:
            return CheckResult(
                "coverage",
                Verdict.FAIL,
                f"duplicate question text: '{it.question[:50]}...'",
            )
        seen_texts.add(it.question)

    return CheckResult(
        "coverage",
        Verdict.PASS,
        f"{len(types)} question types across {len(items)} items",
    )


# ---------------------------------------------------------------------------
# Check registry
# ---------------------------------------------------------------------------

# Per-item checks (single QAItem)
ITEM_CHECKS = [
    check_answer,
    check_params,
    check_unit,
    check_leakage,
    check_degenerate,
    check_tolerance,
]

# Batch checks (list of QAItems)
BATCH_CHECKS = [
    check_coverage,
]

# LLM-assisted checks (require a provider callable, run via CLI --llm flag)
from .llm_checks import LLM_CHECKS  # noqa: E402

# Combined for convenience
ALL_CHECKS = ITEM_CHECKS + BATCH_CHECKS + LLM_CHECKS
