#!/usr/bin/env python3
"""Batch QA pair generation across many seeds with optional LLM humanization.

Generates ~100k simulator-grounded QA items by varying the random seed to
produce diverse component parameter values for each circuit topology.

Phases:
  1. Generation  — sample → simulate → extract facts → generate questions
  2. Humanization — reword questions via DeepSeek (opt-in, --humanize)

Usage:
    uv run python scripts/batch_generate.py --total 100000 --workers 8 -o output/batch
    uv run python scripts/batch_generate.py --total 100000 --workers 8 --humanize -o output/batch
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: Generation (runs in subprocess workers — Xyce subprocess calls)
# ═══════════════════════════════════════════════════════════════════════════════


def _generate_one_seed(
    seed: int, cache_dir: str | None, images_dir: str, topologies: list[str]
) -> list[dict]:
    """Generate QA items for all topologies at a given seed."""
    import os

    os.environ.setdefault("XYCE_QUIET", "1")

    from electronics_qa_generator.extraction.facts import FACT_EXTRACTORS
    from electronics_qa_generator.extraction.parsers import parse_ac, parse_op, parse_tran
    from electronics_qa_generator.questions.generator import generate_questions
    from electronics_qa_generator.simulation.cache import FactCache
    from electronics_qa_generator.simulation.runner import invoke_xyce
    from electronics_qa_generator.templates import ALL_TEMPLATES

    _PARSERS = {"op": parse_op, "ac": parse_ac, "tran": parse_tran}

    by_name = {t.topology: t for t in ALL_TEMPLATES}
    cache = FactCache(cache_dir=Path(cache_dir)) if cache_dir else None
    imgs = Path(images_dir)
    imgs.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    for name in topologies:
        template = by_name[name]
        facts = None
        if cache is not None:
            facts = cache.get(name, seed)

        if facts is None:
            record = template.sample(seed=seed)
            sim_type = record.simulation.type if record.simulation else "op"
            try:
                stdout, rc, converged = invoke_xyce(record.netlist)
            except Exception:
                continue
            if not converged:
                continue
            parser = _PARSERS.get(sim_type, parse_op)
            try:
                parsed = parser(stdout)
            except Exception:
                continue
            extractor = FACT_EXTRACTORS.get(name)
            if extractor is None:
                continue
            try:
                facts = extractor(parsed, record.parameters)
            except Exception:
                continue
            if cache is not None:
                cache.put(name, seed, facts)

        if facts is None:
            continue

        record = template.sample(seed=seed)

        # Render schematic once per (topology, seed)
        schematic_path: str | None = None
        if record.graph is not None:
            seed_str = f"{seed & 0xFFFFFFFF:08x}"
            topo_dir = imgs / name
            topo_dir.mkdir(parents=True, exist_ok=True)
            png_name = f"{seed_str}.png"
            png_path = topo_dir / png_name
            if not png_path.exists():
                try:
                    from electronics_qa_generator.render.schematic import render_schematic
                    render_schematic(record.graph, png_path)
                except Exception:
                    pass
            if png_path.exists():
                schematic_path = f"images/{name}/{png_name}"

        try:
            qa_items = generate_questions(name, facts, record.parameters)
        except Exception:
            continue

        for item in qa_items:
            items.append({
                "topology": name,
                "seed": seed,
                "id": record.id,
                "question_type": item.question_type,
                "question": item.question,
                "answer": item.answer,
                "answer_value": item.answer_value,
                "unit": item.unit,
                "tolerance": item.tolerance,
                "choices": item.choices,
                "program": item.program,
                "explanation": item.explanation,
                "schematic_path": schematic_path,
            })
    return items


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2: Humanization (runs in thread workers — network I/O bound)
# ═══════════════════════════════════════════════════════════════════════════════


def _humanize_one_item(raw_item: dict, cache_dir: str | None, model: str) -> dict:
    """Humanize a single QA item via DeepSeek LLM.

    Thread-safe — each thread imports its own modules. The LLM
    paraphrases the question and optionally generates an explanation,
    but NEVER alters answer/unit/tolerance fields.
    """
    from electronics_qa_generator.llm.cache import HumanizationCache
    from electronics_qa_generator.llm.humanize import humanize_item
    from electronics_qa_generator.models import QAItem

    cache = HumanizationCache(cache_dir=Path(cache_dir)) if cache_dir else None

    item = QAItem(
        question_type=raw_item["question_type"],
        question=raw_item["question"],
        answer=raw_item["answer"],
        answer_value=raw_item["answer_value"],
        unit=raw_item.get("unit"),
        tolerance=raw_item.get("tolerance"),
        choices=raw_item.get("choices"),
        program=raw_item.get("program"),
        explanation=raw_item.get("explanation"),
    )

    humanized = humanize_item(item, cache=cache, explain=True, model=model)

    raw_item["question"] = humanized.question
    raw_item["explanation"] = humanized.explanation
    return raw_item


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def count_qa_per_seed(topologies: list[str]) -> int:
    from electronics_qa_generator.questions.templates import QUESTION_TEMPLATES
    return sum(len(QUESTION_TEMPLATES.get(n, [])) for n in topologies)


def _read_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def _write_jsonl(items: list[dict], path: Path) -> None:
    with open(path, "w") as f:
        for item in items:
            f.write(json.dumps(item, default=str) + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Batch generate QA pairs")
    parser.add_argument("--total", type=int, default=100_000, help="Target QA pairs")
    parser.add_argument("--workers", type=int, default=8, help="Simulation workers")
    parser.add_argument("-o", "--out", type=str, default="output/batch", help="Output directory")
    parser.add_argument("--start-seed", type=int, default=0, help="Starting seed")
    parser.add_argument("--cache-dir", type=str, default="cache", help="Fact cache directory")
    parser.add_argument(
        "--humanize", action="store_true", help="Reword questions via DeepSeek LLM"
    )
    parser.add_argument(
        "--humanize-workers", type=int, default=20, help="LLM parallel threads"
    )
    parser.add_argument(
        "--humanize-cache-dir",
        type=str,
        default="cache/humanize",
        help="Humanization cache directory",
    )
    args = parser.parse_args()

    from electronics_qa_generator.templates import ALL_TEMPLATES

    topologies = sorted(t.topology for t in ALL_TEMPLATES)
    qa_per_seed = count_qa_per_seed(topologies)
    num_seeds = (args.total + qa_per_seed - 1) // qa_per_seed
    expected_total = num_seeds * qa_per_seed

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_output = out_dir / "qa_items.jsonl"
    humanized_output = out_dir / "qa_items_humanized.jsonl"

    # ── Phase 1: Generation ────────────────────────────────────────────

    progress_file = out_dir / "progress.txt"
    completed_seeds: set[int] = set()
    if progress_file.exists():
        completed_seeds = {int(ln.strip()) for ln in progress_file.read_text().splitlines() if ln.strip().isdigit()}

    seeds_to_process = [
        s for s in range(args.start_seed, args.start_seed + num_seeds)
        if s not in completed_seeds
    ]

    print(f"Topologies: {len(topologies)}  |  QA/seed: {qa_per_seed}")
    print(f"Seeds needed: {num_seeds} (~{expected_total} QA pairs)")
    print(f"Already done: {len(completed_seeds)}  |  Remaining: {len(seeds_to_process)}")
    print()

    if seeds_to_process:
        print("── Phase 1: Simulation + Question Generation ──")
        t0 = time.monotonic()
        with open(all_output, "a") as fh, open(progress_file, "a") as pf:
            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                futures = {
                    executor.submit(
                        _generate_one_seed, seed, args.cache_dir,
                        str(out_dir / "images"), topologies,
                    ): seed
                    for seed in seeds_to_process
                }
                done = len(completed_seeds)
                total_items = 0
                for future in as_completed(futures):
                    seed = futures[future]
                    try:
                        items = future.result()
                    except Exception as e:
                        print(f"  [FAIL] seed={seed}: {e}")
                        continue
                    for item in items:
                        fh.write(json.dumps(item, default=str) + "\n")
                    fh.flush()
                    pf.write(f"{seed}\n")
                    pf.flush()
                    done += 1
                    total_items += len(items)
                    elapsed = time.monotonic() - t0
                    rate = total_items / elapsed if elapsed else 0
                    if done % max(1, len(seeds_to_process) // 40) == 0 or done == len(seeds_to_process):
                        print(f"  [{done/len(seeds_to_process)*100:5.1f}%] {done}/{len(seeds_to_process)} "
                              f"seeds | {total_items} items | {rate:.0f}/s | "
                              f"ETA {(expected_total - total_items) / rate / 60 if rate else 0:.1f}m")
        elapsed = time.monotonic() - t0
        print(f"  ✓ Done in {elapsed:.0f}s ({elapsed/60:.1f}m)")
    else:
        print("── Phase 1: All seeds already processed ──")

    # ── Phase 2: Humanization ──────────────────────────────────────────

    if not args.humanize:
        print("\n── No humanization requested (use --humanize) ──")
        total = sum(1 for _ in open(all_output))
        print(f"Final: {total} QA items → {all_output}")
        return

    print(f"\n── Phase 2: LLM Humanization ({args.humanize_workers} threads) ──")

    # Check LLM availability
    from electronics_qa_generator.llm.provider import is_available
    if not is_available():
        print("  ⚠ DeepSeek API key not found — skipping humanization")
        return

    items = _read_jsonl(all_output)
    print(f"  Loaded {len(items)} items from {all_output}")

    # Only humanize items whose question hasn't already been humanized
    # (simple heuristic: already-humanized items have "explanation" set)
    to_humanize = [i for i in items if not i.get("explanation")]
    already = len(items) - len(to_humanize)
    print(f"  Already humanized: {already}  |  To humanize: {len(to_humanize)}")

    if not to_humanize:
        print("  ✓ All items already humanized")
        return

    from electronics_qa_generator.llm.provider import _read_config
    model = _read_config().get("DEEPSEEK_MODEL", "deepseek-v4-pro")

    t0 = time.monotonic()
    done = 0
    with ThreadPoolExecutor(max_workers=args.humanize_workers) as executor:
        futures = {
            executor.submit(_humanize_one_item, item, args.humanize_cache_dir, model): i
            for i, item in enumerate(to_humanize)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                to_humanize[idx] = future.result()
            except Exception:
                pass  # keep original on error
            done += 1
            elapsed = time.monotonic() - t0
            rate = done / elapsed if elapsed else 0
            if done % max(1, len(to_humanize) // 40) == 0 or done == len(to_humanize):
                print(f"  [{done/len(to_humanize)*100:5.1f}%] {done}/{len(to_humanize)} "
                      f"| {rate:.1f} items/s | ETA "
                      f"{(len(to_humanize)-done)/rate/60 if rate else 0:.1f}m")

    # Merge humanized items back with already-done ones
    all_items = [i for i in items if i.get("explanation")] + to_humanize
    _write_jsonl(all_items, humanized_output)

    elapsed = time.monotonic() - t0
    print(f"  ✓ Humanized {done} items in {elapsed:.0f}s ({elapsed/60:.1f}m)")
    print(f"  Output: {humanized_output}")


if __name__ == "__main__":
    main()
