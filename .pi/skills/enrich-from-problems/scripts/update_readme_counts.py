#!/usr/bin/env python3
"""Step 9 — Update README.md with current topology and question template counts.

Usage:
    uv run python .pi/skills/enrich-from-problems/scripts/update_readme_counts.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def get_counts() -> tuple[int, int, list[str]]:
    from electronics_qa_generator.templates import ALL_TEMPLATES
    from electronics_qa_generator.questions.templates import QUESTION_TEMPLATES

    topologies = sorted(t.topology for t in ALL_TEMPLATES)
    n_topos = len(topologies)
    n_questions = sum(len(v) for v in QUESTION_TEMPLATES.values())
    return n_topos, n_questions, topologies


def update_readme(readme_path: Path, n_topos: int, n_questions: int, topologies: list[str]) -> bool:
    text = readme_path.read_text(encoding="utf-8")
    original = text

    # Update "## Available topologies (N)"
    text = re.sub(
        r"(## Available topologies\s*)\(\d+\)",
        rf"\1({n_topos})",
        text,
    )

    # Update topology grid only if a topology is missing from the current grid.
    # This avoids reformatting the hand-curated layout on every run.
    grid_match = re.search(
        r"(## Available topologies[^\n]*\n\n```\n)(.*?)(```)",
        text,
        flags=re.DOTALL,
    )
    if grid_match:
        existing_grid = grid_match.group(2)
        missing = [t for t in topologies if t not in existing_grid]
        if missing:
            # Append new topologies to the existing grid
            new_grid = existing_grid.rstrip("\n") + "  " + "  ".join(missing) + "\n"
            text = text[:grid_match.start(2)] + new_grid + text[grid_match.end(2):]

    # Update "--topologies | all N |" table row
    text = re.sub(
        r"(\|\s*`--topologies`\s*\|\s*all\s*)\d+(\s*\|)",
        rf"\g<1>{n_topos}\g<2>",
        text,
    )

    # Update "N circuit topologies" in the pipeline diagram label
    text = re.sub(
        r"(\d+) circuit topolog",
        rf"{n_topos} circuit topolog",
        text,
    )

    # Update "QA/seed: N" style references
    text = re.sub(
        r"(QA/seed:\s*)\d+",
        rf"\g<1>{n_questions}",
        text,
    )

    if text == original:
        return False
    readme_path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("ERROR: README.md not found. Run from the repo root.", file=sys.stderr)
        sys.exit(1)

    n_topos, n_questions, topologies = get_counts()
    changed = update_readme(readme_path, n_topos, n_questions, topologies)

    print(f"Topologies  : {n_topos}")
    print(f"QA/seed     : {n_questions}")
    if changed:
        print("✓ README.md updated")
    else:
        print("  README.md already up to date")


if __name__ == "__main__":
    main()
