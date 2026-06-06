"""Deterministic answer computation from CLEVR-style programs.

Walks a program's op list, maintaining a result stack, and produces
(answer_value, answer_text, unit, tolerance) tuples.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Unit map: default units for fact/param keys
# ---------------------------------------------------------------------------

_UNITS: dict[str, str | None] = {
    "Vout_dc": "V",
    "Vin_dc": "V",
    "Vout_peak": "V",
    "Vin_amplitude": "V",
    "cutoff_hz": "Hz",
    "center_freq_hz": "Hz",
    "bandwidth_hz": "Hz",
    "passband_gain_db": "dB",
    "peak_gain_db": "dB",
    "divider_ratio": None,
    "ripple_ratio": None,
    "Q": None,
    "ripple_vpp": "V",
    "behavior": None,
}


def _unit_for(key: str) -> str | None:
    return _UNITS.get(key)


# ---------------------------------------------------------------------------
# Program interpreter
# ---------------------------------------------------------------------------


def compute_answer(
    program: list[dict[str, Any]],
    facts: dict[str, Any],
    params: dict[str, Any],
) -> tuple[float | None, str, str | None, float | None]:
    """Evaluate a CLEVR-style program and return the answer tuple.

    Returns:
        (answer_value, answer_text, unit, tolerance)
    """
    stack: list[Any] = []
    pending_precision: int = 3
    last_raw_value: float | None = None

    for step in program:
        op = step["op"]

        if op == "read_fact":
            val = facts.get(step["fact"], 0)
            stack.append(val)
            last_raw_value = float(val) if isinstance(val, (int, float)) else last_raw_value

        elif op == "read_param":
            val = params.get(step["param"], 0)
            stack.append(val)
            last_raw_value = float(val) if isinstance(val, (int, float)) else last_raw_value

        elif op == "push_const":
            stack.append(step["value"])

        elif op == "add":
            b = float(stack.pop())
            a = float(stack.pop())
            result = a + b
            stack.append(result)
            last_raw_value = result

        elif op == "sub":
            b = float(stack.pop())
            a = float(stack.pop())
            result = a - b
            stack.append(result)
            last_raw_value = result

        elif op == "mul":
            b = float(stack.pop())
            a = float(stack.pop())
            result = a * b
            stack.append(result)
            last_raw_value = result

        elif op == "div":
            b = float(stack.pop())
            a = float(stack.pop())
            result = a / b if b != 0 else 0.0
            stack.append(result)
            last_raw_value = result

        elif op == "compare":
            b = stack.pop()
            a = stack.pop()
            operator = step["operator"]
            a_val = float(a)
            b_val = float(b)
            if operator == ">":
                stack.append(a_val > b_val)
            elif operator == "<":
                stack.append(a_val < b_val)
            elif operator == ">=":
                stack.append(a_val >= b_val)
            elif operator == "<=":
                stack.append(a_val <= b_val)
            elif operator == "==":
                stack.append(a_val == b_val)
            else:
                raise ValueError(f"unknown comparison operator: {operator!r}")

        elif op == "classify":
            value = str(stack.pop())
            labels = step["labels"]
            stack.append(value if value in labels else labels[-1] if labels else "unknown")

        elif op == "format_numeric":
            unit = step.get("unit")
            precision = step["precision"]
            value = float(stack.pop())
            pending_precision = precision
            # Round the value so answer_value matches the formatted text.
            # e.g. 0.0005 at precision 3 → 0.001, not 0.0005.
            rounded = round(value, precision)
            last_raw_value = rounded
            if unit:
                stack.append(f"{rounded:.{precision}f} {unit}")
            else:
                stack.append(f"{rounded:.{precision}f}")

        elif op == "return_bool":
            val = stack.pop()
            true_label = step.get("true_label", "yes")
            false_label = step.get("false_label", "no")
            stack.append(true_label if val else false_label)
            last_raw_value = None  # boolean answer — no numeric value

        elif op == "return_label":
            stack.append(str(stack.pop()))
            last_raw_value = None  # label answer — no numeric value

        else:
            raise ValueError(f"unknown program op: {op!r}")

    if not stack:
        return None, "", None, None

    top = stack[-1]

    if last_raw_value is not None:
        # Use the raw numeric value with the formatted text from stack
        text = str(stack[-1]) if stack else ""
        unit = _infer_unit(program)
        tolerance = 0.5 * (10**-pending_precision)
        return last_raw_value, text, unit, tolerance

    if isinstance(top, str):
        return None, str(top), None, None

    value = float(top)
    text = f"{value:.{pending_precision}g}"
    unit = _infer_unit(program)
    if unit:
        text = f"{text} {unit}"

    tolerance = 0.5 * (10**-pending_precision)
    return value, text, unit, tolerance


def _infer_unit(program: list[dict]) -> str | None:
    """Try to infer the unit from program ops.

    Looks for the most recent ``format_numeric`` step with an explicit
    ``unit`` key. If none found, falls back to the unit map from the
    last ``read_fact`` op.
    """
    # Explicit unit from format_numeric takes priority
    for step in reversed(program):
        if step["op"] == "format_numeric":
            return step.get("unit")  # may be None (explicitly unitless)
    # Fall back to fact key inference
    for step in reversed(program):
        if step["op"] == "read_fact":
            return _unit_for(step["fact"])
    return None
