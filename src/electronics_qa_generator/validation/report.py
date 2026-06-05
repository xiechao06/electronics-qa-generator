"""Validation report: aggregates per-item CheckResults into a summary."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .checks import BATCH_CHECKS, ITEM_CHECKS
from .models import CheckResult, Verdict


@dataclass
class ValidationReport:
    """Aggregate report for a validation run on a set of QA items."""

    items: list[list[CheckResult]] = field(default_factory=list)
    batch_results: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when no check has a FAIL verdict."""
        for item_results in self.items:
            for r in item_results:
                if r.verdict == Verdict.FAIL:
                    return False
        for r in self.batch_results:
            if r.verdict == Verdict.FAIL:
                return False
        return True

    @property
    def total_checks(self) -> int:
        return sum(len(rr) for rr in self.items) + len(self.batch_results)

    @property
    def fail_count(self) -> int:
        return self._count(Verdict.FAIL)

    @property
    def warn_count(self) -> int:
        return self._count(Verdict.WARN)

    @property
    def pass_count(self) -> int:
        return self._count(Verdict.PASS)

    def _count(self, verdict: Verdict) -> int:
        n = sum(1 for rr in self.items for r in rr if r.verdict == verdict)
        n += sum(1 for r in self.batch_results if r.verdict == verdict)
        return n

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "stats": {
                "total_checks": self.total_checks,
                "pass": self.pass_count,
                "fail": self.fail_count,
                "warn": self.warn_count,
                "items": len(self.items),
            },
            "fails": [
                {"item": i, "check": r.name, "message": r.message}
                for i, rr in enumerate(self.items)
                for r in rr
                if r.verdict == Verdict.FAIL
            ],
            "warns": [
                {"item": i, "check": r.name, "message": r.message}
                for i, rr in enumerate(self.items)
                for r in rr
                if r.verdict == Verdict.WARN
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    # -- builder -----------------------------------------------------------

    @classmethod
    def from_items(
        cls,
        qa_items: list,
        facts: dict[str, object],
        params: dict[str, object],
        *,
        provider: object = None,
        llm_cache: object = None,
    ) -> ValidationReport:
        """Run all checks on a list of QA items and produce a report.

        If *provider* is given, LLM-assisted checks are also run.
        """
        item_results: list[list[CheckResult]] = []
        for item in qa_items:
            results: list[CheckResult] = []
            for check_fn in ITEM_CHECKS:
                name = check_fn.__name__
                try:
                    import inspect

                    sig = inspect.signature(check_fn)
                    kwargs: dict = {}
                    if "facts" in sig.parameters:
                        kwargs["facts"] = facts
                    if "params" in sig.parameters:
                        kwargs["params"] = params
                    r = check_fn(item, **kwargs)
                except Exception as exc:
                    r = CheckResult(name, Verdict.FAIL, f"check raised: {exc}")
                results.append(r)

            # LLM-assisted checks (opt-in)
            if provider is not None:
                from .llm_checks import LLM_CHECKS

                for check_fn in LLM_CHECKS:
                    try:
                        r = check_fn(item, provider=provider, cache=llm_cache)
                    except Exception as exc:
                        r = CheckResult(
                            check_fn.__name__,
                            Verdict.PASS,
                            f"check raised: {exc}",
                        )
                    results.append(r)

            item_results.append(results)

        # Batch checks
        batch_results: list[CheckResult] = []
        for check_fn in BATCH_CHECKS:
            try:
                r = check_fn(qa_items)
            except Exception as exc:
                r = CheckResult(
                    check_fn.__name__,
                    Verdict.FAIL,
                    f"check raised: {exc}",
                )
            batch_results.append(r)

        return cls(items=item_results, batch_results=batch_results)
