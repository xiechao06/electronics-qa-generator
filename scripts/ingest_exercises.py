#!/usr/bin/env python3
"""Parse exercises_with_circuits.md into per-problem directories.

Each directory gets:
  image.png   — copied from docs/circuit_exercises/images/
  problem.md  — the problem statement
  solution.md — the solution (if present)

Usage:
    uv run python scripts/ingest_exercises.py \
        docs/circuit_exercises/exercises_with_circuits.md \
        --out /tmp/problems
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", title.lower())
    return s.strip("_")[:60]


def parse_blocks(md_text: str) -> list[dict]:
    blocks = re.split(r"(?=^#### )", md_text, flags=re.MULTILINE)
    results = []
    current_chapter = "unknown"
    for block in blocks:
        ch = re.search(r"^## (Chapter \d+[^\n]+)", block, re.MULTILINE)
        if ch:
            current_chapter = ch.group(1).strip()

        title_m = re.search(r"^#### (.+)", block)
        if not title_m:
            continue

        title = title_m.group(1).strip()
        images = re.findall(r"!\[.*?\]\((images/[^)]+)\)", block)
        if not images:
            continue

        # Extract problem text (between **Problem:** and **Solution:** or end)
        problem_text = ""
        prob_m = re.search(
            r"\*\*Problem:\*\*\s*\n(.*?)(?=\n\*\*Solution:\*\*|\n---|\Z)", block, re.DOTALL
        )
        if prob_m:
            problem_text = prob_m.group(1).strip()

        # Extract solution text
        solution_text = ""
        sol_m = re.search(r"\*\*Solution:\*\*\s*\n(.*?)(?=\n---|\Z)", block, re.DOTALL)
        if sol_m:
            solution_text = sol_m.group(1).strip()

        # Skip if no problem text
        if not problem_text:
            continue

        results.append(
            {
                "chapter": current_chapter,
                "title": title,
                "slug": slugify(title),
                "images": images,
                "problem_text": problem_text,
                "solution_text": solution_text,
                "has_solution": bool(solution_text),
            }
        )

    return results


def write_problem_dirs(problems: list[dict], src_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for p in problems:
        slug = p["slug"]
        pdir = out_dir / slug
        pdir.mkdir(exist_ok=True)

        # Copy first image as image.png
        img_src = src_dir / p["images"][0]
        if img_src.exists():
            shutil.copy(img_src, pdir / "image.png")
        else:
            print(f"  WARNING: image not found: {img_src}")

        # Write problem.md
        (pdir / "problem.md").write_text(
            f"# {p['title']}\n\n{p['problem_text']}\n", encoding="utf-8"
        )

        # Write solution.md if present
        if p["has_solution"]:
            (pdir / "solution.md").write_text(
                f"# Solution: {p['title']}\n\n{p['solution_text']}\n", encoding="utf-8"
            )

        # Write metadata
        (pdir / "meta.json").write_text(
            __import__("json").dumps(
                {"title": p["title"], "chapter": p["chapter"], "images": p["images"]},
                indent=2,
            ),
            encoding="utf-8",
        )

        written += 1

    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--out", type=Path, default=Path("/tmp/circuit_problems"))
    args = parser.parse_args()

    src_dir = args.markdown.parent
    text = args.markdown.read_text(encoding="utf-8")
    problems = parse_blocks(text)

    print(f"Found {len(problems)} problems with image + problem text")
    by_chapter: dict[str, int] = {}
    for p in problems:
        by_chapter[p["chapter"]] = by_chapter.get(p["chapter"], 0) + 1
    for ch, n in sorted(by_chapter.items()):
        sol = sum(1 for p in problems if p["chapter"] == ch and p["has_solution"])
        print(f"  {n:3d} ({sol} w/ solution)  {ch}")

    written = write_problem_dirs(problems, src_dir, args.out)
    print(f"\nWrote {written} problem directories to {args.out}")


if __name__ == "__main__":
    main()
