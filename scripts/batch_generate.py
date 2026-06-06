#!/usr/bin/env python3
"""Batch QA pair generation across many seeds with optional LLM humanization.

Generates ~100k simulator-grounded QA items by varying the random seed to
produce diverse component parameter values for each circuit topology.

Phases:
  1. Generation  — sample → simulate → extract facts → generate questions
  2. Humanization — reword questions via DeepSeek (opt-in, --humanize)

Usage:
    uv run python scripts/batch_generate.py --total 100000 --workers 8 -o output/batch
    uv run python scripts/batch_generate.py --total 100000 --topologies voltage_divider,rc_lowpass
    uv run python scripts/batch_generate.py --total 100000 --workers 8 --humanize -o output/batch

Options:
    --total        Target number of QA pairs (default: 100000)
    --topologies   Comma-separated topology names to generate (default: all 14)
                   Use --list-topologies to see available names
    --workers      Parallel simulation worker processes (default: 8)
    --start-seed   First seed value (default: 0)
    --cache-dir    Fact cache directory (default: .cache)
    -o, --out      Output directory (default: output/batch)
    --humanize     Reword questions via DeepSeek LLM (opt-in)
    --list-topologies  Print available topology names and exit
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

    from electronics_qa_generator.extraction.bias import augment_with_dc_bias
    from electronics_qa_generator.extraction.facts import FACT_EXTRACTORS
    from electronics_qa_generator.extraction.parsers import get_parser
    from electronics_qa_generator.questions.generator import generate_questions
    from electronics_qa_generator.simulation.cache import FactCache
    from electronics_qa_generator.simulation.runner import invoke_xyce
    from electronics_qa_generator.templates import ALL_TEMPLATES

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
            parser = get_parser(sim_type, name)
            try:
                parsed = parser(stdout)
            except Exception:
                continue
            parsed = augment_with_dc_bias(parsed, record)
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
                "netlist": record.netlist,
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


def _write_yaml_summary(
    jsonl_path: Path,
    out_dir: Path,
    topologies: list[str],
    num_seeds: int,
    start_seed: int,
) -> None:
    """Generate a human-readable YAML summary of the batch run."""
    import datetime
    from collections import Counter

    import yaml

    items = _read_jsonl(jsonl_path)

    # Per-topology stats
    topo_counts: Counter[str] = Counter()
    topo_qtypes: dict[str, Counter[str]] = {}
    question_types: Counter[str] = Counter()

    # Group all QA items by topology
    items_by_topo: dict[str, list[dict]] = {}
    for item in items:
        topo = item.get("topology", "unknown")
        topo_counts[topo] += 1
        qtype = item.get("question_type", "unknown")
        question_types[qtype] += 1
        if topo not in topo_qtypes:
            topo_qtypes[topo] = Counter()
        topo_qtypes[topo][qtype] += 1
        if topo not in items_by_topo:
            items_by_topo[topo] = []
        items_by_topo[topo].append({
            "id": item.get("id", ""),
            "seed": item.get("seed", 0),
            "question_type": item.get("question_type", ""),
            "question": item.get("question", ""),
            "answer": item.get("answer", ""),
            "answer_value": item.get("answer_value"),
            "unit": item.get("unit"),
            "tolerance": item.get("tolerance"),
            "program": item.get("program"),
            "schematic_path": item.get("schematic_path", ""),
            "netlist": item.get("netlist", ""),
        })

    per_topo = {}
    for topo in sorted(topo_counts):
        per_topo[topo] = {
            "count": topo_counts[topo],
            "question_types": dict(topo_qtypes.get(topo, {})),
            "items": items_by_topo.get(topo, []),
        }

    summary = {
        "run": {
            "timestamp": datetime.datetime.now().isoformat(),
            "command": f"batch_generate.py --total {len(items)} --workers 8 -o {out_dir}",
            "duration_s": None,
        },
        "overview": {
            "total_items": len(items),
            "total_topologies": len(topo_counts),
            "seeds_generated": num_seeds,
            "seed_range": f"{start_seed}–{start_seed + num_seeds - 1}",
            "question_types": dict(question_types),
        },
        "by_topology": per_topo,
        "output": {
            "jsonl": str(jsonl_path),
            "schematics": str(out_dir / "images"),
            "summary_yaml": str(out_dir / "qa_items.yaml"),
        },
    }

    yaml_path = out_dir / "qa_items.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(summary, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"Summary: {yaml_path}")


PROMPT_IMAGE_ONLY_INSTRUCTION = (
    "Do not consult the answer file, the netlist, or any other artifacts. "
    "Answer the following questions purely from the schematic image above:"
)


def _generate_prompt_files(jsonl_path: Path, prompts_dir: Path) -> int:
    """Emit per-schematic prompt and answer Markdown files.

    Reads ``qa_items.jsonl``, groups items by ``(topology, seed)``, and writes
    two files per group::

        prompts/<topology>_<seed>.md          — image ref + image-only questions
        prompts/<topology>_<seed>_answers.md   — numbered ground-truth answers

    Returns the number of (prompt + answer) pairs written.
    """
    from collections import defaultdict

    items = _read_jsonl(jsonl_path)
    if not items:
        return 0

    prompts_dir.mkdir(parents=True, exist_ok=True)

    # Group by (topology, seed)
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for item in items:
        topo = item.get("topology", "unknown")
        seed = item.get("seed", 0)
        groups[(topo, seed)].append(item)

    written = 0
    for (topo, seed), q_items in sorted(groups.items()):
        # Derive the image path from the first item that has one.
        schematic_path = q_items[0].get("schematic_path", "")
        # Make it relative to prompts_dir (prompts/ and images/ are siblings)
        rel_image = f"../{schematic_path}" if schematic_path else ""

        # ── Prompt file ──
        prompt_path = prompts_dir / f"{topo}_{seed:08d}.md"
        lines = []
        if rel_image:
            lines.append(f"![schematic]({rel_image})")
            lines.append("")
        lines.append(PROMPT_IMAGE_ONLY_INSTRUCTION)
        lines.append("")
        for i, qi in enumerate(q_items, start=1):
            question = qi.get("question", "<no question>")
            lines.append(f"{i}. {question}")
            lines.append("")
        prompt_path.write_text("\n".join(lines), encoding="utf-8")

        # ── Answer file ──
        answer_path = prompts_dir / f"{topo}_{seed:08d}_answers.md"
        a_lines = ["# Answers", ""]
        for i, qi in enumerate(q_items, start=1):
            answer = qi.get("answer", "")
            value = qi.get("answer_value")
            unit = qi.get("unit", "")
            tol = qi.get("tolerance")
            parts = [f"{i}. {answer}"]
            if value is not None and unit is not None:
                parts.append(f"   ({value} {unit}")
                if tol is not None:
                    parts.append(f", tolerance ±{tol}")
                parts.append(")")
            a_lines.append("".join(parts))
            a_lines.append("")
        # Append SPICE netlist for context
        netlist = q_items[0].get("netlist", "")
        if netlist:
            a_lines.append("## Netlist")
            a_lines.append("")
            a_lines.append("```spice")
            a_lines.append(netlist.strip())
            a_lines.append("```")
            a_lines.append("")
        answer_path.write_text("\n".join(a_lines), encoding="utf-8")

        written += 1

    return written


def _generate_and_report(jsonl_path: Path, out_dir: Path) -> None:
    """Call ``_generate_prompt_files`` and print a one-line summary."""
    prompts_dir = out_dir / "prompts"
    count = _generate_prompt_files(jsonl_path, prompts_dir)
    print(f"Prompts: {count} prompt/answer pairs → {prompts_dir}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Batch generate QA pairs")
    parser.add_argument("--total", type=int, default=100_000, help="Target QA pairs")
    parser.add_argument(
        "--topologies",
        type=str,
        default=None,
        help="Comma-separated topology names to generate (default: all)",
    )
    parser.add_argument(
        "--list-topologies",
        action="store_true",
        help="Print available topology names and exit",
    )
    parser.add_argument("--workers", type=int, default=8, help="Simulation workers")
    parser.add_argument("-o", "--out", type=str, default="output/batch", help="Output directory")
    parser.add_argument("--start-seed", type=int, default=0, help="Starting seed")
    parser.add_argument("--cache-dir", type=str, default=".cache", help="Fact cache directory")
    parser.add_argument(
        "--humanize", action="store_true", help="Reword questions via DeepSeek LLM"
    )
    parser.add_argument(
        "--humanize-workers", type=int, default=20, help="LLM parallel threads"
    )
    parser.add_argument(
        "--humanize-cache-dir",
        type=str,
        default=".cache/humanize",
        help="Humanization cache directory",
    )
    parser.add_argument(
        "--no-prompts",
        action="store_true",
        help="Skip generating per-schematic prompt/answer Markdown files",
    )
    args = parser.parse_args()

    from electronics_qa_generator.templates import ALL_TEMPLATES

    all_topos = sorted(t.topology for t in ALL_TEMPLATES)

    if args.list_topologies:
        print("Available topologies:")
        for t in all_topos:
            qa_count = count_qa_per_seed([t])
            print(f"  {t:30s} ({qa_count} QA/seed)")
        return

    if args.topologies is not None:
        requested = [t.strip() for t in args.topologies.split(",")]
        invalid = [t for t in requested if t not in all_topos]
        if invalid:
            print(f"Unknown topology(s): {', '.join(invalid)}")
            print(f"Available: {', '.join(all_topos)}")
            raise SystemExit(1)
        topologies = requested
    else:
        topologies = all_topos
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
        _write_yaml_summary(all_output, out_dir, topologies, num_seeds, args.start_seed)
        if not args.no_prompts:
            _generate_and_report(all_output, out_dir)
        return

    print(f"\n── Phase 2: LLM Humanization ({args.humanize_workers} threads) ──")

    # Check LLM availability
    from electronics_qa_generator.llm.provider import is_available
    if not is_available():
        print("  ⚠ DeepSeek API key not found — skipping humanization")
        _write_yaml_summary(all_output, out_dir, topologies, num_seeds, args.start_seed)
        if not args.no_prompts:
            _generate_and_report(all_output, out_dir)
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
        _write_yaml_summary(all_output, out_dir, topologies, num_seeds, args.start_seed)
        if not args.no_prompts:
            _generate_and_report(all_output, out_dir)
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
    _write_yaml_summary(humanized_output, out_dir, topologies, num_seeds, args.start_seed)
    if not args.no_prompts:
        _generate_and_report(humanized_output, out_dir)


if __name__ == "__main__":
    main()
