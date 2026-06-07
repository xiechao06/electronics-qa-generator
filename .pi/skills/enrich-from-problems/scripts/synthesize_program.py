#!/usr/bin/env python3
"""Step 4 — Propose CLEVR-style question templates from facts + problem text.

Usage:
    uv run python .pi/skills/enrich-from-problems/scripts/synthesize_program.py \
        <problem_dir>/facts.json \
        <problem_dir>/problem.md \
        --out <problem_dir>/question_templates.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SYNTHESIS_PROMPT = """\
You are building a CLEVR-style QA dataset for electronics circuits.

Given the simulation fact table and problem statement below, generate a JSON
array of question template entries — one per question in the problem.

Each entry MUST follow this schema exactly:

{
  "id": "<topology>_<short_snake_case_id>",
  "question_type": "<direct | derived | classification | comparison>",
  "question_template": "<natural English question with {param} placeholders for circuit values>",
  "program": [
    {"op": "read_fact", "fact": "<fact_key_from_facts_table>"},
    {"op": "format_numeric", "value": "$0", "unit": "<unit>", "precision": <int>, "min_rel_tol": 0.05}
  ],
  "answer_keys": ["<fact_key>"],
  "answer_formatter": "numeric"
}

Rules:
1. EVERY numerical answer must come from the simulation fact table below.
   Never invent or compute a value — just read it from the facts.
2. The `fact` key in `read_fact` must EXACTLY match a key in the fact table.
3. `question_template` should be exam-style English. Use {{R1_ohm}}, {{C1_F}},
   {{Vin_V}} etc. as placeholders where component values appear in the question.
   Only reference values visible in the circuit schematic image.
4. `question_type`:
   - `direct`: answer is directly a simulation output (voltage, current)
   - `derived`: answer is derived (gain = Vout/Vin, but read from facts, not computed)
   - `classification`: answer is a label (yes/no, lagging/leading, stable/unstable)
   - `comparison`: answer compares two quantities
5. For classification questions, use this program format instead:
   {"op": "classify", "fact": "<key>", "thresholds": [...], "labels": [...]}
6. Use `precision: 3` for voltages/currents, `precision: 1` for dB/degrees,
   `precision: 2` for frequencies/times.
7. The `id` must be unique.

Simulation fact table:
{facts_table}

Problem statement:
{problem_text}

Return ONLY the JSON array. No markdown, no explanation.
"""


def synthesize_with_llm(facts: dict, problem_text: str, topology: str) -> list[dict]:
    """Call LLM to propose question templates."""
    try:
        from electronics_qa_generator.llm.provider import complete
    except ImportError:
        print("ERROR: LLM provider not available.", file=sys.stderr)
        sys.exit(1)

    facts_table = json.dumps(facts, indent=2)
    prompt = SYNTHESIS_PROMPT.format(
        facts_table=facts_table,
        problem_text=problem_text,
        topology=topology,
    )

    response = complete(prompt=prompt, max_tokens=3000, temperature=0.1)
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        templates = json.loads(text)
        if not isinstance(templates, list):
            templates = [templates]
        return templates
    except json.JSONDecodeError as e:
        print(f"ERROR: LLM returned invalid JSON:\n{text}\nParse error: {e}", file=sys.stderr)
        sys.exit(1)


def validate_templates(templates: list[dict], facts: dict) -> list[str]:
    """Return a list of validation warnings."""
    warnings = []
    ids_seen = set()
    for i, t in enumerate(templates):
        tid = t.get("id", f"<missing id #{i}>")
        if tid in ids_seen:
            warnings.append(f"{tid}: duplicate id")
        ids_seen.add(tid)

        # Check all read_fact ops reference known keys
        for step in t.get("program", []):
            if step.get("op") == "read_fact":
                key = step.get("fact", "")
                if key not in facts:
                    warnings.append(f"{tid}: read_fact key '{key}' not in facts table")

        # Check answer_keys
        for key in t.get("answer_keys", []):
            if key not in facts:
                warnings.append(f"{tid}: answer_key '{key}' not in facts table")

    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize CLEVR-style question templates")
    parser.add_argument("facts_json", type=Path, help="Path to facts.json")
    parser.add_argument("problem_md", type=Path, help="Path to problem.md")
    parser.add_argument("--out", type=Path, default=None, help="Output question_templates.json")
    args = parser.parse_args()

    facts_data = json.loads(args.facts_json.read_text(encoding="utf-8"))
    topology = facts_data.get("topology", "unknown")
    facts = facts_data.get("facts", facts_data)  # support flat or nested format

    problem_text = args.problem_md.read_text(encoding="utf-8")
    out_path = args.out or args.facts_json.parent / "question_templates.json"

    print(f"Synthesizing templates for {topology} ({len(facts)} facts, {problem_text.count('?')} questions detected) ...")
    templates = synthesize_with_llm(facts, problem_text, topology)

    # Validate
    warnings = validate_templates(templates, facts)
    if warnings:
        print("\n⚠ Validation warnings (review before registering):")
        for w in warnings:
            print(f"  {w}")
    else:
        print("✓ All program ops reference known fact keys")

    out_path.write_text(json.dumps(templates, indent=2), encoding="utf-8")
    print(f"\nTemplates written: {out_path}")
    print(f"  {len(templates)} template(s) proposed:")
    for t in templates:
        print(f"    [{t.get('question_type','?')}] {t.get('id','?')}")
    print()
    print("Review question_templates.json carefully before proceeding to Step 5/6.")


if __name__ == "__main__":
    main()
