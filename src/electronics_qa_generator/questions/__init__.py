"""Question template engine.

Generates CLEVR-style QA items from extracted simulation facts using
deterministic program execution. The LLM never creates truth — questions
are instantiated from templates, and answers are computed from facts.

Usage::

    from electronics_qa_generator.questions import (
        generate_questions,
        QUESTION_TEMPLATES,
        compute_answer,
    )

    items = generate_questions("rc_lowpass", facts, params)
    for item in items:
        print(item.question, "→", item.answer)
"""

from .compute import compute_answer
from .generator import generate_questions
from .templates import QUESTION_TEMPLATES
from .future_templates import FUTURE_QUESTION_TEMPLATES

__all__ = [
    "QUESTION_TEMPLATES",
    "FUTURE_QUESTION_TEMPLATES",
    "compute_answer",
    "generate_questions",
]
