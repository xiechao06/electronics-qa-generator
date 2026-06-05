"""CLEVR-style program ops and builder helpers.

Each question template carries a ``program`` — an ordered list of dicts
representing a deterministic computation pipeline operating on a stack.

Ops modify the stack:
- ``read_fact`` / ``read_param`` — push a value
- ``push_const`` — push a literal
- ``add`` / ``sub`` / ``mul`` / ``div`` — pop two, push result
- ``compare`` — pop two, push boolean
- ``classify`` — pop one, push label string
- ``format_numeric`` / ``return_bool`` / ``return_label`` — formatting

The ``$N`` references in builder args are documentation only; the interpreter
does not resolve them — it evaluates ops in order using a stack.
"""

from __future__ import annotations

from typing import Any


def read_fact(fact_name: str) -> dict[str, Any]:
    return {"op": "read_fact", "fact": fact_name}


def read_param(param_name: str) -> dict[str, Any]:
    return {"op": "read_param", "param": param_name}


def push_const(value: float) -> dict[str, Any]:
    return {"op": "push_const", "value": value}


def _binary(op_name: str, a: str, b: str) -> dict[str, Any]:
    return {"op": op_name, "a": a, "b": b}


def add(a: str, b: str) -> dict[str, Any]:
    return _binary("add", a, b)


def sub(a: str, b: str) -> dict[str, Any]:
    return _binary("sub", a, b)


def mul(a: str, b: str) -> dict[str, Any]:
    return _binary("mul", a, b)


def div(a: str, b: str) -> dict[str, Any]:
    return _binary("div", a, b)


def compare(operator: str) -> dict[str, Any]:
    """Compare two values on the stack. Pops b then a, pushes (a op b)."""
    return {"op": "compare", "operator": operator}


def classify(value_ref: str, labels: list[str]) -> dict[str, Any]:
    return {"op": "classify", "value": value_ref, "labels": labels}


def format_numeric(
    value_ref: str,
    unit: str | None = None,
    precision: int = 3,
) -> dict[str, Any]:
    return {
        "op": "format_numeric",
        "value": value_ref,
        "unit": unit,
        "precision": precision,
    }


def return_bool(
    value_ref: str,
    true_label: str = "yes",
    false_label: str = "no",
) -> dict[str, Any]:
    return {
        "op": "return_bool",
        "value": value_ref,
        "true_label": true_label,
        "false_label": false_label,
    }


def return_label(value_ref: str) -> dict[str, Any]:
    return {"op": "return_label", "value": value_ref}
