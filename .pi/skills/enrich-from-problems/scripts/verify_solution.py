#!/usr/bin/env python3
"""Step 5 — Compare simulation-derived answers with provided solutions.

Usage:
    uv run python .pi/skills/enrich-from-problems/scripts/verify_solution.py \
        <problem_dir>/facts.json \
        <problem_dir>/solution.md \
        <problem_dir>/question_templates.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# Regex to find numerical answers in solution text: = 3.14 V, = -6.0 dB, ≈ 1.5 kΩ
_ANSWER_RE = re.compile(
    r"(?:=|≈|≃)\s*([+-]?\s*\d+\.?\d*(?:[eE][+-]?\d+)?)\s*"
    r"(mV|µV|uV|kV|V|mA|µA|uA|kA|A|mW|µW|uW|kW|W|"
    r"kHz|MHz|GHz|Hz|kΩ|MΩ|Ω|ohm|ms|µs|us|ns|ps|s|"
    r"dB|°|deg|rad|%|—|[-])?",
    re.IGNORECASE,
)

UNIT_SCALE = {
    "mv": 1e-3, "µv": 1e-6, "uv": 1e-6, "kv": 1e3,
    "ma": 1e-3, "µa": 1e-6, "ua": 1e-6, "ka": 1e3,
    "mw": 1e-3, "µw": 1e-6, "uw": 1e-6, "kw": 1e3,
    "khz": 1e3, "mhz": 1e6, "ghz": 1e9,
    "kΩ": 1e3, "mΩ": 1e6, "kohm": 1e3, "mohm": 1e6,
    "ms": 1e-3, "µs": 1e-6, "us": 1e-6, "ns": 1e-9, "ps": 1e-12,
}


def normalise(value: float, unit: str) -> float:
    return value * UNIT_SCALE.get(unit.lower().strip(), 1.0)


def extract_solution_values(solution_text: str) -> list[tuple[float, str]]:
    """Extract all (value, unit) pairs from solution text."""
    results = []
    for m in _ANSWER_RE.finditer(solution_text):
        raw = m.group(1).replace(" ", "")
        unit = (m.group(2) or "").strip()
        try:
            results.append((normalise(float(raw), unit), unit))
        except ValueError:
            pass
    return results


def get_sim_answer(templates: list[dict], facts: dict) -> dict[str, float]:
    """Compute simulation answers for all templates."""
    answers = {}
    for t in templates:
        tid = t.get("id", "?")
        for step in t.get("program", []):
            if step.get("op") == "read_fact":
                key = step["fact"]
                if key in facts:
                    answers[tid] = facts[key]
                    break
    return answers


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare simulation answers with solutions")
    parser.add_argument("facts_json", type=Path)
    parser.add_argument("solution_md", type=Path)
    parser.add_argument("templates_json", type=Path)
    parser.add_argument("--tol", type=float, default=0.05,
                        help="Relative tolerance for match (default 5%%)")
    args = parser.parse_args()

    facts_data = json.loads(args.facts_json.read_text(encoding="utf-8"))
    facts = facts_data.get("facts", facts_data)

    templates = json.loads(args.templates_json.read_text(encoding="utf-8"))
    solution_text = args.solution_md.read_text(encoding="utf-8")

    sim_answers = get_sim_answer(templates, facts)
    sol_values = extract_solution_values(solution_text)

    print(f"Simulation answers ({len(sim_answers)}):")
    for tid, val in sim_answers.items():
        print(f"  {tid}: {val:.6g}")

    print(f"\nSolution values extracted ({len(sol_values)}):")
    for val, unit in sol_values:
        print(f"  {val:.6g} {unit}")

    if not sol_values:
        print("\nNo numerical values found in solution.md. Nothing to compare.")
        return

    # Pair up by order (best-effort matching for now)
    print(f"\nComparison (tol={args.tol*100:.0f}%):")
    sim_list = list(sim_answers.items())
    for i, (tid, sim_val) in enumerate(sim_list):
        if i < len(sol_values):
            sol_val, sol_unit = sol_values[i]
            if sim_val == 0 and sol_val == 0:
                match = True
            elif sim_val == 0:
                match = abs(sol_val) < 1e-12
            else:
                rel_err = abs(sim_val - sol_val) / abs(sim_val)
                match = rel_err <= args.tol

            status = "✓ MATCH" if match else f"✗ MISMATCH"
            print(f"  {tid}: sim={sim_val:.6g}  solution={sol_val:.6g} {sol_unit}  → {status}")
            if not match:
                print(f"    (relative error: {abs(sim_val-sol_val)/max(abs(sim_val),1e-30)*100:.1f}%)")
                print(f"    → Simulation truth stands. Check if netlist component values are correct.")
        else:
            print(f"  {tid}: sim={sim_val:.6g}  (no solution value to compare)")


if __name__ == "__main__":
    main()
