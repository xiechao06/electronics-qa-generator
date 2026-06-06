---
name: verify-qa-against-agent
description: >
  Verify generated electronics QA items (question + schematic image + netlist +
  ground-truth answer) by having an LLM agent solve each question blind from the
  image, then deterministically grading it against simulation-derived truth.
  Use when the user wants to audit QA quality / answerability, "verify questions
  against an agent", test whether the schematic conveys enough to answer, or
  diagnose netlist/image mismatches. Asks for topologies and the number of
  questions, generates in small bunches, solves image+question with the LLM,
  and on a wrong answer reruns the simulation and asks whether the netlist
  mismatches the question + image.
metadata:
  author: electronics-qa-generator
  version: "1.0"
---

# Verify QA Against an Agent

Audit whether generated QA items are **answerable from what a solver actually
sees** (the schematic image + question text), and whether the image/netlist are
consistent. The agent plays the role of a multimodal LLM solver; a deterministic
script grades its answer against the simulation-derived ground truth.

**Invariant (never violate):** The LLM never creates truth. Simulation +
deterministic code own every answer. Here the LLM is the *examinee*, not the
answer key — it must solve from `image + question` alone, and a script decides
PASS/FAIL. Never let the solver read `answer_key.jsonl` or the netlist before
committing an answer.

**How the blind solve is enforced:** each question is handed to the
`circuit-solver` subagent, which runs in a **fresh context** with only the
`read` tool and is given just the question text + image path. It cannot see
this conversation, the answer key, or the netlist — the no-peek guarantee is
structural, not a promise. You (the orchestrator) drive Steps 1–2 and 4–5 and
delegate only Step 3's solving to that subagent.

All helper paths below are relative to this skill directory
(`.pi/skills/verify-qa-against-agent/`). Run every command from the repo root
with `uv run`.

## Pre-flight: Xyce

Simulation is the source of truth, so Xyce must be installed:

```bash
which Xyce
```

If it is not found, STOP and tell the user:

> Xyce is not installed or not on your PATH. Please install Xyce first
> (https://xyce.sandia.gov/downloads/), then re-run this verification.

## Step 1 — Ask which topologies to verify

List the available topologies (with how many question templates each has):

```bash
uv run eqa questions --list
```

Then **ask the user** which topologies to verify (one, several, or all). Wait
for an answer. Do not assume "all".

## Step 2 — Ask how many questions per topology, generate in small bunches

**Ask the user** how many questions to generate **per topology**. Keep bunches
small (suggest 5–20) so the solve/grade loop stays interactive and reviewable.

For each chosen topology, prepare a batch. This generates the questions, renders
each schematic, and splits the data into a blind **solver view** and a held-back
**answer key**:

```bash
uv run python .pi/skills/verify-qa-against-agent/scripts/prepare_batch.py \
    --topology <TOPOLOGY> --count <N> --start-seed 0 --out .verify/<TOPOLOGY>
```

Outputs under `.verify/<TOPOLOGY>/`:
- `solver_view.jsonl` — `{id, topology, seed, question_type, question, image}`
  (the **only** thing the solver may read)
- `answer_key.jsonl` — ground-truth `answer`, `answer_value`, `unit`,
  `tolerance`, `program`, and `netlist_path` (grader-only; do not read while
  solving)
- `images/<topology>/<seed>.png` — rendered schematics
- `<topology>_<seed>.cir` — netlists (for Step 4 diagnosis only)

If `prepared` is less than requested, some seeds did not converge; mention it
and continue with what was prepared, or raise `--start-seed`/`--count`.

## Step 3 — Solve each question blind (via subagent), then grade

Iterate over the lines of `solver_view.jsonl`. For **each** item:

1. **Delegate the solve to the `circuit-solver` subagent.** Pass only the
   question text and the image path — never the answer, netlist, or program.
   Use the subagent tool in SINGLE mode:

   ```
   subagent(
     agent="circuit-solver",
     task="Image path: <IMAGE>\n\nQuestion: <QUESTION>"
   )
   ```

   The subagent runs in a fresh context with only the `read` tool, so it cannot
   see this conversation or the held-back key. It returns a reply ending in a
   line `ANSWER: <...>`. Extract that answer string.

   You may batch several items in one `subagent` call using `tasks: [...]` (one
   entry per question) to solve a bunch concurrently — keep each task limited to
   its own image path + question.
2. **Grade with the script** (it decides PASS/FAIL, not the solver):

   ```bash
   uv run python .pi/skills/verify-qa-against-agent/scripts/check_answer.py \
       --key .verify/<TOPOLOGY>/answer_key.jsonl \
       --id "<ID>" --answer "<the subagent's ANSWER line>"
   ```

   Exit 0 = PASS, exit 1 = FAIL. The JSON shows ground truth and the diff.

Record each result. If the answer is **correct (PASS)**, move on. If
**incorrect (FAIL)**, go to Step 4 for that item.

## Step 4 — On a wrong answer: rerun simulation, check netlist vs question+image

A wrong answer means one of: (a) the schematic/labels disagree with the netlist
that produced the truth, (b) the image+question genuinely lack the information
needed, or (c) the question is just hard and the item is fine. Diagnose:

1. **Rerun the simulation** for that item's topology + seed to re-confirm the
   ground truth is real and convergent:

   ```bash
   uv run eqa simulate <TOPOLOGY> --seed <SEED> --no-cache
   ```

   If it does not converge, flag the item as `sim_nonconvergent` and stop here.

2. **Ask the LLM: does the netlist match the question + image?** This is a
   diagnosis you (the orchestrator) perform — *not* the blind solver, since it
   requires the netlist. Read the netlist (`<TOPOLOGY>_<SEED>.cir`) and the
   schematic image together, and judge consistency:
   - Does every component + value in the `.cir` appear correctly in the image?
     (e.g. `R1 in out 27k` ⇒ the image shows R1 = 27k between `in` and `out`.)
   - Does the image label the nodes the question references?
   - Could the question be answered from image + question alone, given the
     netlist is the truth?

   Classify the failure as exactly one of:
   - `netlist_image_mismatch` — the rendered schematic disagrees with the
     netlist (wrong/missing value, wrong node, wrong topology). **Rendering or
     template bug.**
   - `unanswerable_from_image` — netlist and image agree, but the value/node the
     answer needs is shown in neither the image nor the question text.
     **Coverage gap** (cross-check `eqa verify-templates`).
   - `hard_but_consistent` — image, netlist, and question are all consistent and
     answerable; the solver simply got it wrong. **Item is fine.**

   For the first two, point the user at the fix: `netlist_image_mismatch` →
   `render/svg/` template or `render/` code; `unanswerable_from_image` →
   `questions/templates.py` + the `FACT_INPUTS` table in
   `validation/template_coverage.py`, then `uv run eqa verify-templates`.

## Step 5 — Report

Summarize per topology and overall:

```
## QA Verification — <TOPOLOGY>  (N items)

Solver accuracy: P/N passed

FAILURES
- <id>  agent="..."  truth="..."   diagnosis: <netlist_image_mismatch|unanswerable_from_image|hard_but_consistent|sim_nonconvergent>
  note: <one line>

Action items
- <file/area to fix per non-"hard_but_consistent" failure>
```

Keep the verdict honest: a solver miss on a consistent, answerable item is **not**
a data defect. Only `netlist_image_mismatch`, `unanswerable_from_image`, and
`sim_nonconvergent` are defects to fix.

## Notes

- The `.verify/` directory is scratch output; it can be deleted between runs.
  Use a fresh `--out` per batch (the script appends if reused).
- Solve at temperature-of-care: read the image carefully and do the arithmetic;
  the point is to catch items a careful solver *cannot* answer, not to chase
  rounding. The grader already allows the item tolerance plus a 1% epsilon.
- Batches are reproducible: same `--start-seed` + `--count` ⇒ same items.
