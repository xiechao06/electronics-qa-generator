"""Validation data models: Verdict enum and CheckResult dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class CheckResult:
    """Result of a single verification check on a QA item."""

    name: str
    verdict: Verdict
    message: str = ""
