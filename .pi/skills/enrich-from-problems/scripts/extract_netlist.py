#!/usr/bin/env python3
"""Step 1 — Extract circuit topology and SPICE netlist from a circuit image + problem text.

Usage:
    uv run python .pi/skills/enrich-from-problems/scripts/extract_netlist.py \
        <problem_dir> --out <problem_dir>/extracted.json

Calls the configured VLM with the image and problem text, asks for a structured
JSON describing topology, components, directives, and models.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path


EXTRACTION_PROMPT = """\
You are an expert electronics engineer and SPICE circuit analyst.

Examine the circuit schematic image and the problem statement below.
Extract a complete, structured description of the circuit that can be used to
write a valid SPICE netlist.

Return ONLY a JSON object with this exact schema — no markdown fences, no extra
text:

{
  "topology": "<kebab-case name, e.g. rc_lowpass, bjt_ce_amplifier>",
  "family": "<one of: passive | amplifier | filter | rectifier | resonance>",
  "description": "<one sentence describing what the circuit does>",
  "components": [
    {
      "ref": "<designator, e.g. R1, C1, Q1, V1>",
      "kind": "<resistor | capacitor | inductor | voltage_source | current_source | bjt | mosfet | diode | op_amp>",
      "pos": "<positive node name>",
      "neg": "<negative node name>",
      "value": "<SI value as a number, e.g. 1000 for 1kΩ, 1e-6 for 1µF>",
      "unit": "<Ω | F | H | V | A | — >",
      "model": "<model name if applicable, else null>"
    }
  ],
  "nodes": ["<list of all non-ground node names>"],
  "ground_node": "0",
  "directives": [
    "<SPICE analysis directive, e.g. .op, .ac lin 50 1 1e6, .tran 1u 1m>"
  ],
  "models": [
    "<full SPICE .model line if needed, else empty list>"
  ],
  "analysis_type": "<op | dc | ac | tran>"
}

Rules:
- Use node name "0" for ground everywhere.
- All values must be plain numbers in SI base units (no k/M/µ suffixes).
- Choose clear, lowercase node names: in, out, base, collector, emitter, vcc, etc.
- The topology name must be unique and descriptive.

Problem statement:
{problem_text}
"""


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def extract_with_llm(image_path: Path, problem_text: str) -> dict:
    """Call VLM provider to extract circuit description."""
    try:
        from electronics_qa_generator.llm.provider import complete
    except ImportError:
        print("ERROR: LLM provider not available. Check uv sync --extra sim", file=sys.stderr)
        sys.exit(1)

    prompt = EXTRACTION_PROMPT.format(problem_text=problem_text)
    img_b64 = encode_image(image_path)

    # Try vision-capable call (image + text)
    response = complete(
        prompt=prompt,
        image_base64=img_b64,
        image_mime="image/png",
        max_tokens=2000,
        temperature=0.1,
    )

    text = response.strip()
    # Strip any accidental markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"ERROR: VLM returned invalid JSON:\n{text}\n\nParse error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract circuit netlist from image + problem text")
    parser.add_argument("problem_dir", type=Path, help="Directory with image.png and problem.md")
    parser.add_argument("--out", type=Path, default=None, help="Output JSON path (default: <problem_dir>/extracted.json)")
    parser.add_argument("--image", type=str, default="image.png", help="Image filename inside problem_dir")
    args = parser.parse_args()

    problem_dir = args.problem_dir.resolve()
    image_path = problem_dir / args.image
    problem_path = problem_dir / "problem.md"
    out_path = args.out or (problem_dir / "extracted.json")

    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    if not problem_path.exists():
        print(f"ERROR: problem.md not found: {problem_path}", file=sys.stderr)
        sys.exit(1)

    problem_text = problem_path.read_text(encoding="utf-8")

    print(f"Extracting circuit from {image_path.name} + problem.md ...")
    result = extract_with_llm(image_path, problem_text)

    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Extracted: {out_path}")
    print(f"  topology : {result.get('topology', '?')}")
    print(f"  family   : {result.get('family', '?')}")
    print(f"  components: {[c['ref'] for c in result.get('components', [])]}")
    print(f"  analysis : {result.get('analysis_type', '?')}")
    print()
    print("Review extracted.json carefully before proceeding to Step 2.")


if __name__ == "__main__":
    main()
