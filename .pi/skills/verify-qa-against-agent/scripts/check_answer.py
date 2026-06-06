#!/usr/bin/env python3
"""Deterministically grade the agent's blind answer against the held-back key.

The agent solves a question from (image + question) alone and passes its raw
answer here. This comparator — not the agent — decides PASS/FAIL, so the
solver cannot rationalize a near-miss into a pass. Simulation + code own the
truth; this script only compares.

Numeric items pass when the agent value is within the item's tolerance of the
ground truth (a small relative epsilon absorbs honest rounding). Label /
boolean items pass on a normalized match.

Usage:
    uv run python scripts/check_answer.py \
        --key .verify/rc_lowpass/answer_key.jsonl \
        --id "rc_lowpass:00000000:1" \
        --answer "1782 Hz"

Prints a JSON verdict to stdout and exits 0 on PASS, 1 on FAIL, 2 on error.
"""

from __future__ import annotations

import argparse
import json
import re


def _load_key(key_path: str, qid: str) -> dict | None:
    with open(key_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("id") == qid:
                return rec
    return None


def _first_number(text: str) -> float | None:
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text.replace(",", ""))
    return float(m.group()) if m else None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--key", required=True, help="answer_key.jsonl path")
    ap.add_argument("--id", required=True, help="question id to grade")
    ap.add_argument("--answer", required=True, help="the agent's raw answer string")
    ap.add_argument(
        "--rel-epsilon",
        type=float,
        default=0.01,
        help="extra relative slack on top of the item tolerance (default 1%%)",
    )
    args = ap.parse_args()

    rec = _load_key(args.key, args.id)
    if rec is None:
        print(json.dumps({"id": args.id, "verdict": "ERROR", "detail": "id not found in key"}))
        return 2

    gt_value = rec.get("answer_value")
    gt_answer = rec.get("answer")
    tol = rec.get("tolerance")

    out: dict = {
        "id": args.id,
        "topology": rec.get("topology"),
        "seed": rec.get("seed"),
        "agent_answer": args.answer,
        "ground_truth": gt_answer,
    }

    if isinstance(gt_value, (int, float)):
        a = _first_number(args.answer)
        if a is None:
            out.update(verdict="FAIL", detail="no number found in agent answer")
            print(json.dumps(out))
            return 1
        abs_tol = float(tol) if isinstance(tol, (int, float)) else 0.0
        allow = max(abs_tol, args.rel_epsilon * abs(gt_value))
        diff = abs(a - gt_value)
        ok = diff <= allow
        out.update(
            verdict="PASS" if ok else "FAIL",
            agent_value=a,
            ground_truth_value=gt_value,
            abs_diff=diff,
            allowed=allow,
        )
        print(json.dumps(out))
        return 0 if ok else 1

    # Non-numeric (label / boolean / classification).
    gt_norm = _normalize(str(gt_answer))
    a_norm = _normalize(args.answer)
    ok = gt_norm == a_norm or gt_norm in a_norm or a_norm in gt_norm
    out.update(verdict="PASS" if ok else "FAIL", detail="normalized string match")
    print(json.dumps(out))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
