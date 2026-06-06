#!/usr/bin/env python3
"""Batch-grade blind solver answers for one topology.

Reads ``solver_view.jsonl`` and a directory of solver replies (one file per
question, named ``<sanitized-id>.txt`` where ':' -> '_'), extracts the final
``ANSWER:`` line from each reply, and grades it against ``answer_key.jsonl``
using the exact same comparator as ``check_answer.py``.

Prints a per-item table and a JSON summary (counts + the list of FAIL ids with
their agent answer and ground truth) so the orchestrator can diagnose only the
failures.

Usage:
    uv run python scripts/grade_batch.py --dir .verify/<TOPOLOGY> --sols .verify/<TOPOLOGY>/sols
"""

from __future__ import annotations

import argparse
import json
import os
import re


def _first_number(text: str) -> float | None:
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text.replace(",", ""))
    return float(m.group()) if m else None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_answer(reply: str) -> str | None:
    """Return the text after the last ``ANSWER:`` marker in a reply."""
    matches = list(re.finditer(r"ANSWER\s*:\s*(.+)", reply, re.IGNORECASE))
    if not matches:
        return None
    return matches[-1].group(1).strip()


def _grade(answer: str, rec: dict, rel_epsilon: float = 0.01) -> dict:
    gt_value = rec.get("answer_value")
    gt_answer = rec.get("answer")
    tol = rec.get("tolerance")
    out: dict = {"agent_answer": answer, "ground_truth": gt_answer}
    if isinstance(gt_value, (int, float)) and not isinstance(gt_value, bool):
        a = _first_number(answer)
        if a is None:
            out.update(verdict="FAIL", detail="no number in answer")
            return out
        abs_tol = float(tol) if isinstance(tol, (int, float)) else 0.0
        allow = max(abs_tol, rel_epsilon * abs(gt_value))
        diff = abs(a - gt_value)
        out.update(
            verdict="PASS" if diff <= allow else "FAIL",
            agent_value=a,
            ground_truth_value=gt_value,
            abs_diff=diff,
            allowed=allow,
        )
        return out
    gt_norm = _normalize(str(gt_answer))
    a_norm = _normalize(answer)
    ok = gt_norm == a_norm or gt_norm in a_norm or a_norm in gt_norm
    out.update(verdict="PASS" if ok else "FAIL", detail="normalized string match")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True, help="batch dir with solver_view.jsonl + answer_key.jsonl")
    ap.add_argument("--sols", required=True, help="dir of <sanitized-id>.txt replies")
    args = ap.parse_args()

    keys: dict[str, dict] = {}
    with open(os.path.join(args.dir, "answer_key.jsonl")) as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                keys[rec["id"]] = rec

    rows = []
    with open(os.path.join(args.dir, "solver_view.jsonl")) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    npass = nfail = nmissing = 0
    failures = []
    for row in rows:
        qid = row["id"]
        sol_path = os.path.join(args.sols, qid.replace(":", "_") + ".txt")
        if not os.path.exists(sol_path):
            nmissing += 1
            print(f"MISSING  {qid}")
            continue
        reply = open(sol_path).read()
        answer = _extract_answer(reply)
        if answer is None:
            nfail += 1
            failures.append({"id": qid, "agent_answer": "<no ANSWER line>", "ground_truth": keys[qid].get("answer")})
            print(f"FAIL     {qid}  (no ANSWER line)")
            continue
        res = _grade(answer, keys[qid])
        if res["verdict"] == "PASS":
            npass += 1
            print(f"PASS     {qid}  agent={answer!r}  truth={res['ground_truth']!r}")
        else:
            nfail += 1
            failures.append({
                "id": qid,
                "question": row.get("question"),
                "agent_answer": answer,
                "ground_truth": res.get("ground_truth"),
                "detail": res.get("detail", ""),
            })
            print(f"FAIL     {qid}  agent={answer!r}  truth={res['ground_truth']!r}")

    summary = {
        "topology": rows[0]["topology"] if rows else None,
        "total": len(rows),
        "pass": npass,
        "fail": nfail,
        "missing": nmissing,
        "failures": failures,
    }
    print("\nSUMMARY " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
