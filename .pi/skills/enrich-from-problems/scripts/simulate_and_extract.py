#!/usr/bin/env python3
"""Step 3 — Run Xyce simulation on circuit.sp and extract simulation facts.

Usage:
    uv run python .pi/skills/enrich-from-problems/scripts/simulate_and_extract.py \
        <problem_dir>/circuit.sp \
        --topology <topology_name> \
        --out <problem_dir>/facts.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_xyce() -> str:
    xyce = shutil.which("Xyce")
    if xyce:
        return xyce
    # Common non-standard install locations
    candidates = [
        "/usr/local/XyceNF_7.10/bin/Xyce",
        "/usr/local/Xyce/bin/Xyce",
        "/opt/Xyce/bin/Xyce",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    print("ERROR: Xyce not found. Install Xyce or put it on PATH.", file=sys.stderr)
    print("See: https://xyce.sandia.gov/downloads/", file=sys.stderr)
    sys.exit(1)


def run_xyce(netlist_path: Path, workdir: Path) -> Path:
    """Run Xyce and return path to output file."""
    xyce = find_xyce()
    result = subprocess.run(
        [xyce, str(netlist_path)],
        cwd=str(workdir),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Xyce STDERR:", result.stderr[-2000:], file=sys.stderr)
        print(f"ERROR: Xyce exited with code {result.returncode}", file=sys.stderr)
        sys.exit(1)

    # Xyce writes <netlist_name>.prn or similar
    out_files = list(workdir.glob("*.prn")) + list(workdir.glob("*.csv"))
    if not out_files:
        print("ERROR: Xyce produced no output file.", file=sys.stderr)
        print("STDOUT:", result.stdout[-1000:], file=sys.stderr)
        sys.exit(1)
    return out_files[0]


def parse_prn(prn_path: Path) -> dict[str, list[float]]:
    """Parse a Xyce .prn file into column arrays."""
    columns: dict[str, list[float]] = {}
    header: list[str] = []
    with open(prn_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("*"):
                continue
            if line.startswith("Index"):
                header = re.split(r"\s+", line)
                for h in header:
                    columns[h] = []
                continue
            if line == "End of Xyce(TM) Simulation":
                break
            parts = re.split(r"\s+", line)
            for h, v in zip(header, parts):
                try:
                    columns.setdefault(h, []).append(float(v))
                except ValueError:
                    pass
    return columns


def extract_facts_from_columns(columns: dict, analysis_type: str) -> dict:
    """Extract a flat fact dict from parsed simulation columns."""
    facts: dict = {}

    for col, values in columns.items():
        if col == "Index" or not values:
            continue
        # Normalise column name: V(out) → Vout, I(R1) → IR1
        key = col.replace("(", "").replace(")", "").replace(",", "_")

        if analysis_type == "op":
            # DC operating point: single value
            facts[f"{key}_dc"] = values[0]

        elif analysis_type == "ac":
            # AC sweep: last point (or single point)
            facts[f"{key}_ac"] = values[-1]

        elif analysis_type in ("dc", "tran"):
            # Sweep: store first, last, and all
            facts[f"{key}_first"] = values[0]
            facts[f"{key}_last"] = values[-1]
            facts[f"{key}_max"] = max(values)
            facts[f"{key}_min"] = min(values)

    return facts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Xyce and extract simulation facts")
    parser.add_argument("netlist", type=Path, help="Path to .sp netlist file")
    parser.add_argument("--topology", type=str, default="unknown", help="Topology name (for labelling)")
    parser.add_argument("--out", type=Path, default=None, help="Output facts.json path")
    parser.add_argument("--analysis", type=str, default=None,
                        help="Analysis type (op|dc|ac|tran) — auto-detected if omitted")
    args = parser.parse_args()

    netlist_path = args.netlist.resolve()
    out_path = args.out or netlist_path.parent / "facts.json"

    if not netlist_path.exists():
        print(f"ERROR: Netlist not found: {netlist_path}", file=sys.stderr)
        sys.exit(1)

    # Auto-detect analysis type from netlist
    netlist_text = netlist_path.read_text(encoding="utf-8").lower()
    analysis_type = args.analysis
    if not analysis_type:
        if ".tran" in netlist_text:
            analysis_type = "tran"
        elif ".ac" in netlist_text:
            analysis_type = "ac"
        elif ".dc" in netlist_text:
            analysis_type = "dc"
        else:
            analysis_type = "op"

    print(f"Running Xyce on {netlist_path.name} (analysis: {analysis_type}) ...")

    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        # Copy netlist to workdir
        import shutil as sh
        sh.copy(netlist_path, workdir / netlist_path.name)
        prn_path = run_xyce(workdir / netlist_path.name, workdir)
        columns = parse_prn(prn_path)
        facts = extract_facts_from_columns(columns, analysis_type)

    result = {
        "topology": args.topology,
        "analysis_type": analysis_type,
        "facts": facts,
    }
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Facts written: {out_path}")
    print(f"  {len(facts)} facts extracted:")
    for k, v in sorted(facts.items()):
        print(f"    {k}: {v}")
    print()
    print("Review facts.json before proceeding to Step 4.")


if __name__ == "__main__":
    main()
