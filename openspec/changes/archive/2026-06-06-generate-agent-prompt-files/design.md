## Context

`scripts/batch_generate.py` produces `qa_items.jsonl` (the authoritative session
output) and `qa_items.yaml` (a by-topology summary). Schematic images are written
per-topology under `images/<topology>/<seed>.png`. The user wants to manually
verify QA items by feeding them to an external agent (Perplexity, ChatGPT, etc.),
but today that requires matching images to questions one-by-one — a friction that
makes regular verification unlikely.

The output directory already contains everything needed: JSONL records keyed by
`(topology, seed)`, and image files in a parallel directory tree. The task is to
repackage this into an agent-friendly format — nothing about the pipeline itself
changes.

## Goals / Non-Goals

**Goals:**
- Emit paired `.md` files (prompt + answer) per `(topology, seed)` pair.
- Each prompt lists every question for that image in numbered form with the image
  referenced as a relative Markdown link.
- Each answer file provides the matching numbered ground-truth answers.
- Gated behind a `--prompts` flag so existing workflows are unchanged.
- Single function, called near the end of `main()`, that reads the final JSONL
  and writes the files.

**Non-Goals:**
- No changes to the pipeline stages, simulation, netlist emission, or question
  generation.
- No AI integration — the files are for the human operator to paste into an
  agent of their choice.
- No PDF, HTML, or other export format (just Markdown).
- No fancy directory nesting beyond `prompts/<topology>_<seed>.md` /
  `prompts/<topology>_<seed>_answers.md`.

## Decisions

### 1. Flat prompt directory under the output root

**Files:** `output/batch/prompts/<topology>_<seed>.md` and
`output/batch/prompts/<topology>_<seed>_answers.md`.

**Why:** A flat directory is trivial to browse and to script. The seed is
already embedded in the filename, and the topology name is the prefix — sorting
by name groups images by topology naturally.

**Alternative considered:** `prompts/<topology>/<seed>.md` would mirror the
images tree but adds nesting for no real benefit since filenames are unique
across topologies.

### 2. Image reference uses a relative path to the sibling directory

**Format:** `![schematic](../images/<topology>/<seed>.png)`.

**Why:** When the Markdown is rendered in an application that supports relative
paths (Obsidian, Typora, GitHub preview), the image displays inline. The path
remains valid regardless of where the output tree is moved, as long as
`prompts/` and `images/` stay siblings.

**Alternative considered:** Absolute paths would break if the output is moved.
Embedded base64 would balloon file sizes and is not agent-friendly.

### 3. One prompt file per (topology, seed), not one per question

**Why:** A single schematic image is shared by every question at that seed.
Splitting questions across multiple prompt files per seed would duplicate the
image reference and force the verifier to re-read the same schematic.

### 4. Answer file is a separate `.md` file, not inlined

**Why:** The user pastes the prompt file into the agent; the answer file stays
local for comparison. Keeping them separate prevents accidental leakage of
answers into the agent prompt.

### 5. Post-processing step reads the already-written JSONL

**Why:** By the time prompts are generated, `qa_items.jsonl` is fully written
and on disk. Reading it back avoids threading concerns and works identically
whether humanization was enabled or not (the final JSONL is the canonical
output in both cases).

## Risks / Trade-offs

- **Large output directories:** 200 seeds × 14 topologies = 2,800 prompt files.
  At ~3 KB each this is ~8 MB — negligible. For 10,000 items it remains
  manageable. → No action needed.
- **Forward-compatibility:** If the JSONL schema changes (new fields), the
  prompt generator must be updated. → The function reads only the minimal
  fields (`topology`, `seed`, `id`, `question`, `answer`, `answer_value`,
  `unit`, `schematic_path`) and ignores unknown fields, so new fields are
  invisible to it.
- **Answer file format drift:** If the ground-truth format evolves, answer
  files may lose detail. → Answer includes `value` + `unit` + `tolerance` as a
  single line; future fields can be appended without breaking parsers.

## Open Questions

- Should we also emit a combined "all answers" file for batch grading? → Not
  yet; users can `grep` the answer files if needed.
- Should `--prompts` be the default? → No; keep it opt-in for the first
  iteration to avoid breaking existing workflows.
