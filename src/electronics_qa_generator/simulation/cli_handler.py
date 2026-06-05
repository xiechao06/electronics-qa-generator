"""Handler for the `eqa simulate` subcommand.

Drives: sample template → check cache → run Xyce → parse → extract facts
→ compute richness → cache → print JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ..extraction.facts import FACT_EXTRACTORS
from ..extraction.parsers import parse_ac, parse_op, parse_tran
from ..extraction.scoring import compute_richness
from ..simulation.models import SimResult
from ..templates import ALL_TEMPLATES
from .cache import FactCache
from .runner import check_xyce_installed, invoke_xyce

_PARSERS = {"op": parse_op, "ac": parse_ac, "tran": parse_tran}


def run_simulate(args) -> None:
    """Execute `eqa simulate` logic from parsed CLI args."""
    seed: int = args.seed
    cache_dir: Path | None = Path(args.cache_dir) if args.cache_dir else None
    use_cache: bool = not args.no_cache

    cache = FactCache(cache_dir=cache_dir) if use_cache else None

    by_name = {t.topology: t for t in ALL_TEMPLATES}
    valid_names = sorted(by_name.keys())

    if args.list:
        for name in valid_names:
            print(name)
        return

    topologies: list[str]
    if args.all:
        topologies = valid_names
    elif args.topology:
        topologies = [args.topology]
    else:
        print("error: specify a topology, use --list, or use --all", file=sys.stderr)
        raise SystemExit(2)

    try:
        check_xyce_installed()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1)

    for name in topologies:
        if name not in by_name:
            print(
                f"error: unknown topology '{name}'. Valid: {', '.join(valid_names)}",
                file=sys.stderr,
            )
            raise SystemExit(2)

        template = by_name[name]

        # Check cache
        if cache is not None:
            cached = cache.get(name, seed)
            if cached is not None:
                record = template.sample(seed=seed)
                result = {
                    "topology": name,
                    "seed": seed,
                    "id": record.id,
                    "parameters": record.parameters,
                    "facts": cached,
                    "cached": True,
                }
                print(json.dumps(result, indent=2, default=str))
                continue

        # Sample and simulate
        record = template.sample(seed=seed)
        sim_type = record.simulation.type if record.simulation else "op"

        stdout, rc, converged = invoke_xyce(record.netlist)

        if not converged:
            result = {
                "topology": name,
                "seed": seed,
                "id": record.id,
                "error": "simulation did not converge",
                "exit_code": rc,
                "facts": {},
                "richness": 0.0,
            }
            print(json.dumps(result, indent=2))
            continue

        # Parse
        parser = _PARSERS.get(sim_type, parse_op)
        parsed = parser(stdout)

        # Extract facts
        extractor = FACT_EXTRACTORS.get(name)
        if extractor is None:
            print(
                f"error: no fact extractor for topology '{name}'",
                file=sys.stderr,
            )
            raise SystemExit(2)

        facts = extractor(parsed, record.parameters)

        # Cache
        if cache is not None:
            cache.put(name, seed, facts)

        sim_result = SimResult(
            success=True,
            sim_type=sim_type,
            raw_output=stdout,
            exit_code=rc,
            converged=True,
        )
        score = compute_richness(facts, sim_result)

        result = {
            "topology": name,
            "seed": seed,
            "id": record.id,
            "parameters": record.parameters,
            "simulation_type": sim_type,
            "facts": facts,
            "richness": score.total,
            "cached": False,
        }
        print(json.dumps(result, indent=2, default=str))
