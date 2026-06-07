#!/usr/bin/env python3
"""Step 2 — Emit a SPICE netlist from extracted.json.

Usage:
    uv run python .pi/skills/enrich-from-problems/scripts/emit_netlist.py \
        <problem_dir>/extracted.json --out <problem_dir>/circuit.sp
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

KIND_TO_SPICE = {
    "resistor": "R",
    "capacitor": "C",
    "inductor": "L",
    "voltage_source": "V",
    "current_source": "I",
    "bjt": "Q",
    "mosfet": "M",
    "diode": "D",
    "op_amp": "X",  # subcircuit
}


def format_value(value, kind: str) -> str:
    """Format a numeric value for SPICE (no suffix, plain float)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    # Use engineering notation for readability
    if abs(v) >= 1e9:
        return f"{v/1e9:.6g}g"
    if abs(v) >= 1e6:
        return f"{v/1e6:.6g}Meg"
    if abs(v) >= 1e3:
        return f"{v/1e3:.6g}k"
    if abs(v) == 0:
        return "0"
    if abs(v) < 1e-12:
        return f"{v/1e-15:.6g}f"
    if abs(v) < 1e-9:
        return f"{v/1e-12:.6g}p"
    if abs(v) < 1e-6:
        return f"{v/1e-9:.6g}n"
    if abs(v) < 1e-3:
        return f"{v/1e-6:.6g}u"
    if abs(v) < 1:
        return f"{v/1e-3:.6g}m"
    return f"{v:.6g}"


def emit_component(comp: dict) -> str:
    ref = comp["ref"]
    kind = comp.get("kind", "resistor")
    pos = comp.get("pos", "in")
    neg = comp.get("neg", "0")
    value = comp.get("value", 0)
    model = comp.get("model")

    letter = KIND_TO_SPICE.get(kind, "X")

    if kind == "bjt":
        # Q<ref> <collector> <base> <emitter> <model>
        collector = comp.get("collector", pos)
        base = comp.get("base", "base")
        emitter = comp.get("emitter", neg)
        model_name = model or "Q2N2222"
        return f"Q{ref.lstrip('Q')} {collector} {base} {emitter} {model_name}"

    if kind == "mosfet":
        drain = comp.get("drain", pos)
        gate = comp.get("gate", "gate")
        source = comp.get("source", neg)
        bulk = comp.get("bulk", "0")
        model_name = model or "NMOS1"
        return f"M{ref.lstrip('M')} {drain} {gate} {source} {bulk} {model_name}"

    if kind == "voltage_source":
        val_str = format_value(value, kind)
        return f"{ref} {pos} {neg} DC {val_str}"

    if kind == "current_source":
        val_str = format_value(value, kind)
        return f"{ref} {pos} {neg} DC {val_str}"

    val_str = format_value(value, kind)
    return f"{letter}{ref.lstrip(letter)} {pos} {neg} {val_str}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit SPICE netlist from extracted.json")
    parser.add_argument("extracted_json", type=Path, help="Path to extracted.json")
    parser.add_argument("--out", type=Path, default=None, help="Output .sp path (default: sibling circuit.sp)")
    args = parser.parse_args()

    extracted = json.loads(args.extracted_json.read_text(encoding="utf-8"))
    out_path = args.out or args.extracted_json.parent / "circuit.sp"

    topology = extracted.get("topology", "unknown")
    description = extracted.get("description", "")
    components = extracted.get("components", [])
    directives = extracted.get("directives", [])
    models = extracted.get("models", [])

    lines = [f"* {topology} — {description}"]

    # Model cards first
    for model_line in models:
        lines.append(model_line)

    # Components
    for comp in components:
        lines.append(emit_component(comp))

    # Analysis directives
    for directive in directives:
        lines.append(directive)

    lines.append(".end")

    netlist = "\n".join(lines)
    out_path.write_text(netlist, encoding="utf-8")
    print(f"Netlist written: {out_path}")
    print()
    print(netlist)
    print()
    print("Review circuit.sp before proceeding to Step 3.")


if __name__ == "__main__":
    main()
