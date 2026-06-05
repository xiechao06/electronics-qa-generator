"""Handler for the `eqa validate` subcommand.

Runs the full pipeline, generates QA items, runs static checks, and prints
a validation report.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ..extraction.facts import FACT_EXTRACTORS
from ..extraction.parsers import parse_ac, parse_op, parse_tran
from ..questions.generator import generate_questions
from ..questions.templates import QUESTION_TEMPLATES
from ..simulation.cache import FactCache
from ..simulation.runner import check_xyce_installed, invoke_xyce
from ..templates import ALL_TEMPLATES
from .report import ValidationReport

_PARSERS = {"op": parse_op, "ac": parse_ac, "tran": parse_tran}


def run_validate(args) -> None:
    """Execute `eqa validate` logic."""
    seed: int = args.seed
    cache_dir: Path | None = Path(args.cache_dir) if args.cache_dir else None
    use_cache: bool = not args.no_cache

    by_name = {t.topology: t for t in ALL_TEMPLATES}
    valid_names = sorted(by_name.keys())

    if args.list:
        for name in valid_names:
            count = len(QUESTION_TEMPLATES.get(name, []))
            print(f"{name}: {count} question template(s)")
        return

    if args.topology is None:
        print("error: specify a topology or use --list", file=sys.stderr)
        raise SystemExit(2)

    name = args.topology
    if name not in by_name:
        print(
            f"error: unknown topology '{name}'. Valid: {', '.join(valid_names)}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    cache = FactCache(cache_dir=cache_dir) if use_cache else None

    # Check cache first
    facts: dict | None = None
    if cache is not None:
        facts = cache.get(name, seed)

    if facts is None:
        # Need to simulate
        check_xyce_installed()

        template = by_name[name]
        record = template.sample(seed=seed)
        sim_type = record.simulation.type if record.simulation else "op"

        stdout, rc, converged = invoke_xyce(record.netlist)

        if not converged:
            print(f"error: simulation did not converge (rc={rc})", file=sys.stderr)
            raise SystemExit(1)

        from ..extraction.parsers import parse_op

        parser = _PARSERS.get(sim_type, parse_op)
        parsed = parser(stdout)

        extractor = FACT_EXTRACTORS.get(name)
        if extractor is None:
            print(f"error: no fact extractor for '{name}'", file=sys.stderr)
            raise SystemExit(2)

        facts = extractor(parsed, record.parameters)

        if cache is not None:
            cache.put(name, seed, facts)

    # Re-sample to get params
    template = by_name[name]
    record = template.sample(seed=seed)

    items = generate_questions(name, facts, record.parameters)

    # Run validation (with optional LLM and visual checks)
    provider = None
    llm_cache = None
    vision_provider = None
    vision_cache = None
    if getattr(args, "llm", False):
        from ..llm.provider import is_available

        if is_available():
            provider = True  # signal to use default provider
            from .llm_checks import LLMCheckCache

            llm_cache = LLMCheckCache(cache_dir=cache_dir / "llm_checks" if cache_dir else None)
    if getattr(args, "visual", False):
        vision_provider = True
        from .visual_checks import VisualCheckCache

        vision_cache = VisualCheckCache(
            cache_dir=cache_dir / "visual_checks" if cache_dir else None
        )

    report = ValidationReport.from_items(
        items,
        facts,
        record.parameters,
        provider=provider,
        llm_cache=llm_cache,
        vision_provider=vision_provider,
        vision_cache=vision_cache,
    )

    if getattr(args, "json", False):
        print(report.to_json())
    else:
        print(f"Validation report for {name} (seed {seed})")
        print(f"  Items: {len(items)}")
        print(f"  Total checks: {report.total_checks}")
        print(f"  Pass: {report.pass_count}  Fail: {report.fail_count}  Warn: {report.warn_count}")
        print(f"  Overall: {'OK' if report.ok else 'FAIL'}")

        for i, results in enumerate(report.items):
            fails = [r for r in results if r.verdict.value != "pass"]
            if fails:
                print(f"  Item {i}:")
                for r in fails:
                    print(f"    [{r.verdict.value.upper()}] {r.name}: {r.message}")

        for r in report.batch_results:
            if r.verdict.value != "pass":
                print(f"  Batch: [{r.verdict.value.upper()}] {r.name}: {r.message}")

    # Exit code: 1 on any FAIL
    if not report.ok:
        raise SystemExit(1)
