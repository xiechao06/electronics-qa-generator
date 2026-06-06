# AGENTS.md

Guidance for AI coding agents working in this repository.

## What this project is

A pipeline that generates **multimodal electronics circuit Q/A items** with
**SPICE/Xyce-grounded ground-truth answers**, for an MMMU-style benchmark.
Inspired by **CLEVR** (questions backed by executable programs) and **AutoCkt**
(simulator-in-the-loop as the source of truth).

Read these before doing design work:

- `docs/plan.md` — the full plan (circuit families, sims, question taxonomy, MVP)
- `docs/architecture.md` — end-to-end architecture and data flow
- `docs/circuit_qa_program_language.md` — CLEVR-style DSL for QA programs
- `docs/clevr_explained.md`, `docs/autockt_explained.md`, `docs/papers.md` — background

## The non-negotiable invariant

> **The LLM never creates truth. Simulation establishes facts, code derives
> answers, and the LLM only paraphrases/explains/tags after the answer is fixed.**

When implementing question or answer logic:

- Compute every numeric answer from simulation output or deterministic code.
- Never ask an LLM for a value, a behavior label, or a correct option.
- Every QA item should carry a machine-readable program (CLEVR-style) and a
  traceable link back to a fact in the extracted fact table.

## Tooling

- **Build/env:** `uv` only. Do not use `pip`/`poetry`/`conda`.
- **Python:** pinned to **3.14** via `.python-version`. Do not change without asking.
- Common commands:
  - `uv sync` — install (dev tools included)
  - `uv run eqa ...` — run the CLI
  - `uv run pytest` — tests
  - `uv run ruff check .` and `uv run ruff format .` — lint/format
- Add runtime deps with `uv add <pkg>`; dev deps with `uv add --dev <pkg>`.
  Prefer the existing optional-dependency extras (`sim`, `data`, `render`) for
  stage-specific heavy deps rather than adding them to base `dependencies`.

## Code organization

One subpackage per pipeline stage under `src/electronics_qa_generator/`:

```
templates → sampling → netlist → simulation → parsing → extraction
  → questions → llm → validation → rendering → output
```

- Shared data structures live in `models.py` (`CircuitRecord`, `QAItem`,
  `Sample`). Extend these rather than inventing parallel record shapes.
- End-to-end flow lives in `pipeline.py`. Keep stages decoupled and testable in
  isolation.
- The CLI lives in `cli.py` (the `eqa` console script). Wire new capabilities in
  as subcommands.

## Conventions

- Target Python 3.14; use modern typing (`X | None`, builtin generics, no
  `from __future__` needed except where already present for consistency).
- Keep functions deterministic where they touch ground truth; isolate randomness
  in `sampling/` behind explicit seeds for reproducibility.
- Every accepted sample must be **reproducible from stored metadata** (seed +
  template + parameters), per the architecture doc.
- Add a focused test under `tests/` for each stage you implement.

## Working style

- This is an MVP being built **step by step**. Implement one stage at a time; do
  not scaffold large speculative subsystems.
- Start from the MVP scope in `docs/plan.md` §9 (5 families, `.op/.dc/.ac/.tran`,
  4 question types) before expanding.
- Keep `mmmu_electronics*/` reference data read-only; treat it as the target
  schema, not something to modify.
- Run `uv run pytest` and `uv run ruff check .` before declaring work done.

## Pre-flight check: Xyce

**Before running any pipeline stage that invokes simulation** (emit + simulate,
batch generation, or anything that calls `invoke_xyce`), check whether Xyce is
installed:

```bash
which Xyce
```

If Xyce is not found, **do not attempt to run the pipeline**. Instead, tell the
user:

> Xyce is not installed or not on your PATH. Please install Xyce first, then
> re-run this command. See https://xyce.sandia.gov/downloads/

Do not try to work around a missing Xyce — simulation is the sole source of
truth and no QA items can be generated without it.

## Pipeline

The eqa CLI executes a five-stage pipeline:

```
emit → simulate → questions → validate → assemble
```

| Stage | Command | What it does |
|-------|---------|--------------|
| emit | `eqa emit` | Sample templates, emit SPICE netlist + JSON record |
| simulate | `eqa simulate` | Run Xyce simulation, extract ground-truth facts |
| questions | `eqa questions` | Generate Q/A items from simulation facts |
| validate | `eqa validate` | Run static checks on generated QA items |
| assemble | `eqa assemble` | Assemble full MMMU-compatible dataset |

All commands use `uv run eqa <subcommand>`.

### Common workflows

**Single topology, all stages:**

```bash
uv run eqa emit <topology> --seed 42 -o output/<topology> --render
uv run eqa simulate <topology> --seed 42
uv run eqa questions <topology> --seed 42 -o output/<topology>
uv run eqa validate <topology> --seed 42       # optional
uv run eqa assemble -o dataset
```

**All topologies:**

```bash
uv run eqa emit --all --seed 42 -o output --render
uv run eqa simulate --all --seed 42
# questions doesn't support --all; use scripts/batch_generate.py instead
uv run eqa validate --all --seed 42
```

**High-throughput batch generation:**

```bash
# All topologies, 100k QA pairs
uv run python scripts/batch_generate.py --total 100000 --workers 8 -o output/batch

# Specific topologies only
uv run python scripts/batch_generate.py --total 5000 --topologies voltage_divider,rc_lowpass

# List available topologies with QA-per-seed counts
uv run python scripts/batch_generate.py --list-topologies
```

### Batch generation options

| Option | Default | Description |
|---|---|---|
| `--total` | 100000 | Target number of QA pairs |
| `--topologies` | all 14 | Comma-separated topology names |
| `--list-topologies` | — | Print topologies with QA/seed counts and exit |
| `--workers` | 8 | Parallel simulation worker processes |
| `--start-seed` | 0 | First seed value for reproducible sampling |
| `--cache-dir` | `cache/` | Fact cache directory; speeds repeated runs |
| `-o, --out` | `output/batch/` | Output directory |
| `--humanize` | off | Reword questions via DeepSeek LLM (opt-in, slow) |

The script generates diverse QA items by running many seeds through the
pipeline in parallel. Each seed produces one parameter sample per topology.
Results are cached by netlist content hash so re-running with overlapping
seed ranges is near-instant. Output is a single `qa_items.jsonl` with
per-topology schematic images in `images/<topology>/`.

### Key options by stage

**emit:** `--render` (schematic PNG), `--seed N`, `-o DIR`

**simulate:** `--cache-dir DIR` (speed up repeated runs), `--no-cache`

**questions:** `--jsonl` (one JSON per line), `-o DIR` (schematic output dir).
The `--humanize` flag rewrites questions via LLM but is **deprecated** in
favor of hand-written humanized templates in `questions/templates.py`.

**validate:** `--llm` (LLM-assisted checks), `--visual` (VLM schematic checks),
`--json` (report as JSON)

**assemble:** `-o DIR` (default: `dataset/`)

### Seed reproducibility

Every sample is reproducible from (seed + template + parameters). Use the
same `--seed` across emit/simulate/questions for consistency, or vary it
for diverse parameter samples.

### Cache strategy

Simulation results are cached by netlist content hash under `cache/` (or
`--cache-dir`). Use `--no-cache` to skip. The fact cache is shared across
stages — `eqa questions` reads from the same cache `eqa simulate` writes to.

### Visual checks (opt-in)

`eqa validate --visual` runs two checks via a local Ollama VLM:
- `topology_match` — schematic matches stated topology
- `label_visibility` — component labels are readable

Setup:
```bash
brew install ollama          # one-time
ollama serve                   # start service (localhost:11434)
ollama pull deepseek-vl2-tiny  # ~4 GB, one-time
```

`.env` defaults:
```env
VISION_BASE_URL=http://localhost:11434/v1
VISION_MODEL=deepseek-vl2-tiny
```

When Ollama is not running, visual checks return PASS silently — they are
advisory (WARN), never blocking.

**Behavioral rule:** When asked to generate QA pairs (batch script, any
pipeline stage that produces schematics), or to validate with `--verify`,
and `--visual` was not explicitly mentioned, **always ask**:

> Would you also like to run visual checks on the schematics (Ollama VLM)?

Ask this even if Ollama is not installed or not running — the user may want
to set it up. Do not assume silence means no.

### Troubleshooting

| Problem | Likely fix |
|---------|-----------|
| Xyce not found | Install Xyce or ensure it's on PATH |
| Import errors | `uv sync --extra sim --extra data --extra render` |
| No templates listed | Check `src/electronics_qa_generator/templates/` |
| Simulation non-convergence | Try a different seed for different component values |
