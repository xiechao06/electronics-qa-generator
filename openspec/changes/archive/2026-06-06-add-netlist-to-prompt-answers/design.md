## Context

`_generate_prompt_files` in `scripts/batch_generate.py` already writes answer
files with numbered answers, values, units, and tolerances. The SPICE netlist
for each schematic is available in the JSONL as the `netlist` field on every
QA item (items sharing a schematic share the same netlist).

## Goals / Non-Goals

**Goals:**
- Append a `## Netlist` section to each answer `.md` file containing the SPICE
  netlist for that schematic.

**Non-Goals:**
- No changes to prompt files (netlist remains hidden from the agent).
- No changes to directory structure, naming, or the `--prompts` flag behavior.

## Decisions

### 1. Extract netlist from the first QA item in each group

All items sharing a `(topology, seed)` also share the same schematic and
netlist. Reading it from the first item in the group is sufficient and avoids
repetition.

### 2. Format as a fenced code block under `## Netlist`

**Why:** Markdown code fences are readable, render correctly in previews, and
don't interfere with the numbered answer format above.

## Risks / Trade-offs

- None. A single-line addition per answer file, zero performance impact.
