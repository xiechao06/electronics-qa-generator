"""Question generator: bridges fact tables to QAItem records.

Takes a topology name, extracted facts, and component parameters,
and produces a list of ``QAItem`` records using the question template
registry and deterministic answer computation.
"""

from __future__ import annotations

from ..models import QAItem
from .compute import compute_answer
from .templates import QUESTION_TEMPLATES

# Re-use SPICE formatting for readable question text
from ..graph.spice_emitter import (
    _fmt_capacitance,
    _fmt_frequency,
    _fmt_inductance,
    _fmt_resistance,
    _fmt_voltage,
)

_PARAM_FORMATTERS = {
    "_ohm": _fmt_resistance,
    "_f": _fmt_capacitance,
    "_h": _fmt_inductance,
    "_hz": _fmt_frequency,
    "_dc": _fmt_voltage,
    "_amplitude": _fmt_voltage,
    "_kohm": lambda v: f"{v:.2g}",
    "_mh": lambda v: f"{v:.3g}",
}


def generate_questions(
    topology: str,
    facts: dict,
    params: dict,
) -> list[QAItem]:
    """Generate all QA items for a circuit topology.

    Args:
        topology: Template topology name (e.g. "rc_lowpass").
        facts: Fact dict from simulation + extraction.
        params: Component parameter dict from the circuit record.

    Returns:
        List of populated QAItem records, one per question template.

    Raises:
        KeyError: If the topology is not in QUESTION_TEMPLATES.
    """
    templates = QUESTION_TEMPLATES[topology]

    # Merge facts and params for template text formatting
    context = dict(params)
    context.update(facts)

    items: list[QAItem] = []
    for tmpl in templates:
        # Compute answer
        answer_value, answer_text, unit, tolerance = compute_answer(
            tmpl["program"],
            facts,
            params,
        )

        # Fill question text placeholders from context
        question_text = tmpl["question_template"]
        # Fill {param} placeholders with formatted values
        # Build a formatted context where param values are human-readable
        formatted_context: dict[str, str] = {}
        for key, val in context.items():
            if isinstance(val, (int, float)):
                # Check if we have a formatter for this key suffix
                formatted = str(val)
                for suffix, fmt_fn in _PARAM_FORMATTERS.items():
                    if key.endswith(suffix):
                        formatted = fmt_fn(val)
                        break
                formatted_context[key] = formatted
            else:
                formatted_context[key] = str(val)

        try:
            question_text = question_text.format_map(formatted_context)
        except KeyError, ValueError:
            pass

        # Classification / label answers get choices
        choices: list[str] | None = None
        qtype = tmpl["question_type"]
        if qtype == "classification":
            # Extract labels from the classify op
            for op in tmpl["program"]:
                if op["op"] == "classify":
                    choices = list(op.get("labels", []))
                    break

        items.append(
            QAItem(
                question_type=qtype,
                question=question_text,
                answer=answer_text,
                answer_value=answer_value,
                unit=unit,
                tolerance=tolerance,
                choices=choices,
                program=list(tmpl["program"]),
                explanation=None,
            ),
        )

    return items
