"""Validation stage: static QA-item quality checks.

The verifier runs deterministic checks on every generated QA item before it
enters the dataset. All checks are pure functions — no I/O, no LLM.
"""

from .checks import ALL_CHECKS
from .models import CheckResult, Verdict
from .report import ValidationReport

__all__ = ["ALL_CHECKS", "CheckResult", "Verdict", "ValidationReport"]
