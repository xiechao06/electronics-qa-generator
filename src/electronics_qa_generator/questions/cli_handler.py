"""Handler for the `eqa questions` subcommand.

Runs full pipeline: sample → simulate (or cache) → extract facts → generate
questions → print QA items as JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ..extraction.facts import FACT_EXTRACTORS
from ..extraction.parsers import parse_ac, parse_op, parse_tran
from ..llm.cache import HumanizationCache
from ..llm.humanize import humanize_item
from ..llm.provider import is_available
from ..simulation.cache import FactCache
from ..simulation.runner import check_xyce_installed, invoke_xyce
from ..templates import ALL_TEMPLATES
from .generator import generate_questions
from .templates import QUESTION_TEMPLATES

_PARSERS = {"op": parse_op, "ac": parse_ac, "tran": parse_tran}


def run_questions(args) -> None:
    """Execute `eqa questions` logic."""
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

        parser = _PARSERS.get(sim_type, parse_op)
        parsed = parser(stdout)

        extractor = FACT_EXTRACTORS.get(name)
        if extractor is None:
            print(f"error: no fact extractor for '{name}'", file=sys.stderr)
            raise SystemExit(2)

        facts = extractor(parsed, record.parameters)

        if cache is not None:
            cache.put(name, seed, facts)

    # Re-sample to get params for template text
    template = by_name[name]
    record = template.sample(seed=seed)

    items = generate_questions(name, facts, record.parameters)

    # Humanize (opt-in)
    if getattr(args, "humanize", False):
        if is_available():
            hcache = HumanizationCache(cache_dir=cache_dir / "humanize" if cache_dir else None)
        else:
            hcache = None
        items = [humanize_item(item, cache=hcache) for item in items]

    # Print as JSON array or JSONL
    result = [
        {
            "question_type": item.question_type,
            "question": item.question,
            "answer": item.answer,
            "answer_value": item.answer_value,
            "unit": item.unit,
            "tolerance": item.tolerance,
            "choices": item.choices,
            "program": item.program,
            "explanation": item.explanation,
        }
        for item in items
    ]

    if args.jsonl:
        for obj in result:
            print(json.dumps(obj, default=str))
    else:
        print(json.dumps(result, indent=2, default=str))
