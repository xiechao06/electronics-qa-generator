"""Handler for the `eqa assemble` subcommand.

Runs the full pipeline for all 5 topologies, assembles MMMU-compatible JSONL,
and bundles schematics into a self-contained output directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ..extraction.facts import FACT_EXTRACTORS
from ..extraction.parsers import parse_ac, parse_op, parse_tran
from ..questions.generator import generate_questions
from ..simulation.cache import FactCache
from ..simulation.runner import check_xyce_installed, invoke_xyce
from ..templates import ALL_TEMPLATES
from .assembler import assemble_dataset

_PARSERS = {"op": parse_op, "ac": parse_ac, "tran": parse_tran}


def run_assemble(args) -> None:
    """Execute `eqa assemble` logic."""
    seed: int = args.seed
    out_dir = Path(args.out)
    cache_dir: Path | None = Path(args.cache_dir) if args.cache_dir else None
    use_cache: bool = not args.no_cache

    out_dir.mkdir(parents=True, exist_ok=True)

    # Clear any existing dataset.jsonl
    jsonl_path = out_dir / "dataset.jsonl"
    if jsonl_path.exists():
        jsonl_path.unlink()

    check_xyce_installed()

    all_items: list = []
    report_data: dict = {"topologies": {}}

    for template in ALL_TEMPLATES:
        name = template.topology
        cache = FactCache(cache_dir=cache_dir) if use_cache else None

        # Simulation
        facts: dict | None = None
        if cache is not None:
            facts = cache.get(name, seed)

        if facts is None:
            record = template.sample(seed=seed)
            sim_type = record.simulation.type if record.simulation else "op"

            stdout, rc, converged = invoke_xyce(record.netlist)
            if not converged:
                print(f"  [{name}] simulation did not converge — skipping", file=sys.stderr)
                continue

            parser = _PARSERS.get(sim_type, parse_op)
            parsed = parser(stdout)

            extractor = FACT_EXTRACTORS.get(name)
            if extractor is None:
                print(f"  [{name}] no extractor — skipping", file=sys.stderr)
                continue

            facts = extractor(parsed, record.parameters)
            if cache is not None:
                cache.put(name, seed, facts)

        # Re-sample for params
        record = template.sample(seed=seed)
        items = generate_questions(name, facts, record.parameters)

        # Render schematic
        schematic_path: str | None = None
        if record.graph is not None:
            try:
                from ..render.schematic import render_schematic

                images_dir = out_dir / "images" / name
                images_dir.mkdir(parents=True, exist_ok=True)
                seed_str = f"{seed & 0xFFFFFFFF:08x}"
                png_path = images_dir / f"{seed_str}.png"
                render_schematic(record.graph, png_path)
                schematic_path = f"images/{name}/{seed_str}.png"
            except ImportError:
                pass

        # Assemble items for this topology
        schem_paths = [schematic_path] * len(items) if schematic_path else [None] * len(items)
        assemble_dataset(items, schem_paths, name, seed, out_dir)
        all_items.extend(items)

        # Quick validation
        try:
            from ..validation.report import ValidationReport

            vr = ValidationReport.from_items(items, facts, record.parameters)
            report_data["topologies"][name] = {
                "items": len(items),
                "total_checks": vr.total_checks,
                "pass": vr.pass_count,
                "fail": vr.fail_count,
                "warn": vr.warn_count,
                "ok": vr.ok,
            }
        except Exception:
            report_data["topologies"][name] = {"items": len(items)}

        print(f"  [{name}] {len(items)} items assembled")

    # Write validation report
    report_data["total_items"] = len(all_items)
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report_data, indent=2, default=str))

    print(f"\nDone: {len(all_items)} items → {out_dir.resolve()}")
    print(f"  {jsonl_path}")
    print(f"  {report_path}")
