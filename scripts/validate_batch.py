"""Validate a batch JSONL QA output file using static checks.

Usage:
    uv run python scripts/validate_batch.py [--jsonl FILE] [--json] [--cache-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from electronics_qa_generator.models import QAItem
from electronics_qa_generator.simulation.cache import FactCache
from electronics_qa_generator.validation.checks import (
    BATCH_CHECKS,
    ITEM_CHECKS,
    CheckResult,
    Verdict,
)


def load_items(jsonl_path: Path) -> list[dict]:
    items = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate batch JSONL QA output")
    parser.add_argument(
        "--jsonl",
        default="output/batch/qa_items.jsonl",
        help="Path to batch JSONL file (default: output/batch/qa_items.jsonl)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON",
    )
    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Fact cache directory (default: cache/)",
    )
    args = parser.parse_args()

    jsonl_path = Path(args.jsonl)
    if not jsonl_path.exists():
        print(f"error: {jsonl_path} not found", file=sys.stderr)
        raise SystemExit(2)

    raw_items = load_items(jsonl_path)
    print(f"Loaded {len(raw_items)} items from {jsonl_path}")

    cache = FactCache(cache_dir=Path(args.cache_dir))

    # Group items by topology for batch checks
    items_by_topology: defaultdict[str, list[tuple[dict, dict | None, dict | None]]] = defaultdict(
        list
    )

    cache_hits = 0
    cache_misses = 0

    for raw in raw_items:
        topology = raw.get("topology", "unknown")
        seed = raw.get("seed", 0)

        # Look up facts from cache
        facts = cache.get(topology, seed)
        if facts is not None:
            cache_hits += 1
        else:
            cache_misses += 1
            facts = {}

        # Params are not in cache, but we don't need them for most checks
        params = {}

        items_by_topology[topology].append((raw, facts, params))

    if cache_misses > 0:
        print(f"Warning: {cache_misses} items had no cached facts (checks may be skipped)")

    # --- Run per-item checks ---
    total_pass = 0
    total_fail = 0
    total_warn = 0
    all_fails: list[dict] = []
    all_warns: list[dict] = []

    for topology, group in items_by_topology.items():
        for raw, facts, params in group:
            for check_fn in ITEM_CHECKS:
                name = check_fn.__name__

                # Build item for checks that need it
                item = QAItem(
                    question_type=raw.get("question_type", "direct"),
                    question=raw.get("question", ""),
                    answer=raw.get("answer", ""),
                    answer_value=raw.get("answer_value"),
                    unit=raw.get("unit"),
                    tolerance=raw.get("tolerance"),
                    program=raw.get("program"),
                    explanation=raw.get("explanation"),
                    choices=raw.get("choices"),
                )

                # Build kwargs based on what the check expects
                import inspect

                sig = inspect.signature(check_fn)
                kwargs: dict = {}
                if "facts" in sig.parameters:
                    kwargs["facts"] = facts
                if "params" in sig.parameters:
                    kwargs["params"] = params

                try:
                    result = check_fn(item, **kwargs)
                except Exception as exc:
                    result = CheckResult(name, Verdict.FAIL, f"check raised: {exc}")

                if result.verdict == Verdict.FAIL:
                    total_fail += 1
                    all_fails.append(
                        {
                            "topology": topology,
                            "id": raw.get("id", ""),
                            "seed": raw.get("seed"),
                            "check": name,
                            "message": result.message,
                        }
                    )
                elif result.verdict == Verdict.WARN:
                    total_warn += 1
                    all_warns.append(
                        {
                            "topology": topology,
                            "id": raw.get("id", ""),
                            "seed": raw.get("seed"),
                            "check": name,
                            "message": result.message,
                        }
                    )
                else:
                    total_pass += 1

    # --- Run batch checks per topology ---
    for topology, group in items_by_topology.items():
        topo_items: list[QAItem] = []
        for raw, _, _ in group:
            item = QAItem(
                question_type=raw.get("question_type", "direct"),
                question=raw.get("question", ""),
                answer=raw.get("answer", ""),
                answer_value=raw.get("answer_value"),
                unit=raw.get("unit"),
                tolerance=raw.get("tolerance"),
                program=raw.get("program"),
                explanation=raw.get("explanation"),
                choices=raw.get("choices"),
            )
            topo_items.append(item)

        for check_fn in BATCH_CHECKS:
            name = check_fn.__name__
            try:
                result = check_fn(topo_items)
            except Exception as exc:
                result = CheckResult(name, Verdict.FAIL, f"check raised: {exc}")

            if result.verdict == Verdict.FAIL:
                total_fail += 1
                all_fails.append(
                    {
                        "topology": topology,
                        "id": "batch",
                        "check": name,
                        "message": result.message,
                    }
                )
            elif result.verdict == Verdict.WARN:
                total_warn += 1
                all_warns.append(
                    {
                        "topology": topology,
                        "id": "batch",
                        "check": name,
                        "message": result.message,
                    }
                )
            else:
                total_pass += 1

    total = total_pass + total_fail + total_warn
    report = {
        "ok": total_fail == 0,
        "stats": {
            "total_items": len(raw_items),
            "total_topologies": len(items_by_topology),
            "total_checks": total,
            "pass": total_pass,
            "fail": total_fail,
            "warn": total_warn,
        },
        "fails": all_fails,
        "warns": all_warns,
    }

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print()
        print("=" * 60)
        print("  VALIDATION REPORT")
        print("=" * 60)
        print(f"  Items:     {len(raw_items):>8}")
        print(f"  Topologies: {len(items_by_topology):>8}")
        print(f"  Checks:    {total:>8}")
        print(f"  Pass:      {total_pass:>8}")
        print(f"  Fail:      {total_fail:>8}")
        print(f"  Warn:      {total_warn:>8}")
        print(f"  Overall:   {'OK' if total_fail == 0 else 'FAIL'}")
        print("=" * 60)

        if all_fails:
            print(f"\n  FAILS ({len(all_fails)}):")
            for f in all_fails:
                print(f"    [{f['topology']}] {f['check']}: {f['message']}")

        if all_warns:
            print(f"\n  WARNS ({len(all_warns)}):")
            for w in all_warns[:20]:  # limit warns output
                print(f"    [{w['topology']}] {w['check']}: {w['message']}")
            if len(all_warns) > 20:
                print(f"    ... and {len(all_warns) - 20} more")

    if total_fail > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
