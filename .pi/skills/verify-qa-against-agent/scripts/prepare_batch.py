#!/usr/bin/env python3
"""Prepare a verification batch for the agent-as-solver workflow.

Generates a small bunch of QA items for one topology and splits them into:

  - ``solver_view.jsonl``  — what a blind solver is allowed to see: the
    question text and the absolute path to the schematic image. **No answer,
    no netlist.**
  - ``answer_key.jsonl``   — ground truth held back from the solver: the
    deterministic answer, value, unit, tolerance, the QA program, and the
    path to the netlist that produced it (for the mismatch-diagnosis stage).

The split is the whole point: the agent must commit to an answer from the
(image + question) pair alone, then a deterministic comparator grades it
against the held-back key. The LLM never sees ground truth before answering,
and never creates it — simulation + code own every answer.

Usage:
    uv run python scripts/prepare_batch.py \
        --topology rc_lowpass --count 10 \
        --start-seed 0 --out .verify/rc_lowpass

Appends to existing solver_view.jsonl/answer_key.jsonl if rerun with the same
--out (use a fresh --out per run for a clean batch).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run_eqa(args: list[str]) -> str:
    """Run an ``eqa`` subcommand and return stdout, raising on failure."""
    proc = subprocess.run(
        ["eqa", *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(
            f"eqa {' '.join(args)} failed (rc={proc.returncode}). "
            "If this is a Xyce error, ensure Xyce is installed and on PATH."
        )
    return proc.stdout


def _emit_netlist(topology: str, seed: int, out: Path, cache_dir: Path) -> str:
    """Emit netlist + schematic for a seed; return the netlist .cir path."""
    _run_eqa(["emit", topology, "--seed", str(seed), "-o", str(out), "--render"])
    cir = out / f"{topology}_{seed & 0xFFFFFFFF:08x}.cir"
    return str(cir)


def _questions(topology: str, seed: int, out: Path, cache_dir: Path) -> list[dict]:
    """Generate QA items for a seed as a list of dicts (one per template)."""
    stdout = _run_eqa(
        [
            "questions",
            topology,
            "--seed",
            str(seed),
            "-o",
            str(out),
            "--cache-dir",
            str(cache_dir),
            "--jsonl",
        ]
    )
    items: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topology", required=True, help="topology name (see: eqa questions --list)")
    ap.add_argument("--count", type=int, required=True, help="number of questions to prepare")
    ap.add_argument("--start-seed", type=int, default=0, help="first seed (default 0)")
    ap.add_argument("--out", required=True, help="output directory for this batch")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cache_dir = out / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    solver_fp = out / "solver_view.jsonl"
    key_fp = out / "answer_key.jsonl"

    collected = 0
    seed = args.start_seed
    # Bound the seed scan so a degenerate topology can't loop forever.
    max_seed = args.start_seed + max(args.count * 8, 64)

    with solver_fp.open("a") as sv, key_fp.open("a") as ak:
        while collected < args.count and seed < max_seed:
            try:
                cir_path = _emit_netlist(args.topology, seed, out, cache_dir)
                items = _questions(args.topology, seed, out, cache_dir)
            except SystemExit:
                # Non-convergent seed (or transient sim issue): skip to next.
                seed += 1
                continue

            for idx, item in enumerate(items):
                if collected >= args.count:
                    break
                qid = f"{args.topology}:{seed & 0xFFFFFFFF:08x}:{idx}"
                rel_img = item.get("schematic_path")
                abs_img = str((out / rel_img).resolve()) if rel_img else None

                solver_rec = {
                    "id": qid,
                    "topology": args.topology,
                    "seed": seed,
                    "question_type": item.get("question_type"),
                    "question": item.get("question"),
                    "image": abs_img,
                }
                key_rec = {
                    "id": qid,
                    "topology": args.topology,
                    "seed": seed,
                    "answer": item.get("answer"),
                    "answer_value": item.get("answer_value"),
                    "unit": item.get("unit"),
                    "tolerance": item.get("tolerance"),
                    "choices": item.get("choices"),
                    "program": item.get("program"),
                    "image": abs_img,
                    "netlist_path": cir_path,
                }
                sv.write(json.dumps(solver_rec, default=str) + "\n")
                ak.write(json.dumps(key_rec, default=str) + "\n")
                collected += 1

            seed += 1

    summary = {
        "topology": args.topology,
        "requested": args.count,
        "prepared": collected,
        "solver_view": str(solver_fp),
        "answer_key": str(key_fp),
        "seeds_used": list(range(args.start_seed, seed)),
    }
    print(json.dumps(summary, indent=2))
    if collected < args.count:
        sys.stderr.write(
            f"\nWARNING: only prepared {collected}/{args.count} "
            "(ran out of converging seeds in scan window).\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
