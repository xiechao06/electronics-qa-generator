---
name: eqa-pipeline
description: Execute the electronics QA generation pipeline (emit → simulate → questions → validate → assemble). Use when the user wants to generate circuit QA items, run the pipeline, or work through pipeline stages.
license: MIT
metadata:
  author: eqa
  version: "1.0"
---

Execute the electronics QA generation pipeline using the `eqa` CLI. This
pipeline generates simulator-grounded electronics circuit Q/A items for an
MMMU-style benchmark.

**Non-negotiable invariant**: The LLM never creates truth. Simulation
establishes facts, code derives answers, and the LLM only
paraphrases/explains/tags after the answer is fixed.

## Pipeline overview

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

## Available topologies

```
half_wave_rectifier    rc_highpass    rc_lowpass
rlc_bandpass           voltage_divider
```

## Common workflows

### Quick single-topology run (all stages)

```bash
# 1. Emit netlist + render schematic
uv run eqa emit <topology> --seed 42 -o output/<topology> --render

# 2. Simulate
uv run eqa simulate <topology> --seed 42

# 3. Generate questions
uv run eqa questions <topology> --seed 42 -o output/<topology>

# 4. Validate (optional)
uv run eqa validate <topology> --seed 42

# 5. Assemble (when ready to package)
uv run eqa assemble -o dataset
```

### Run all topologies

```bash
# Emit all templates
uv run eqa emit --all --seed 42 -o output --render

# Simulate all
uv run eqa simulate --all --seed 42

# Generate questions for all
uv run eqa questions --all --seed 42 -o output

# Validate all
uv run eqa validate --all --seed 42
```

### Full pipeline with LLM humanization and verification

```bash
uv run eqa questions <topology> --seed 42 -o output --humanize --verify --llm
```

### List available resources

```bash
uv run eqa emit --list          # list available topologies
uv run eqa simulate --list      # same
uv run eqa questions --list     # list topologies with question counts
```

## Key options by stage

### emit
- `--render` — render schematic PNG alongside netlist/JSON
- `--seed N` — set random seed for reproducibility
- `-o DIR` — output directory (default: stdout)

### simulate
- `--cache-dir DIR` — fact cache directory to speed up repeated runs
- `--no-cache` — skip cache read/write

### questions
- `--humanize` — rewrite questions in natural exam-style language via DeepSeek
- `--verify` — run static validation checks on generated QA items
- `--llm` — run LLM-assisted checks (requires `--verify`)
- `--jsonl` — output one JSON object per line
- `-o DIR` — output directory for rendered schematics

### validate
- `--llm` — run LLM-assisted checks (ambiguity, leakage, difficulty)
- `--visual` — run vision-model checks on schematic images using local Ollama
  (`deepseek-vl2-tiny`). Requires Ollama installed and running. See setup below.
- `--json` — output report as JSON

### assemble
- `-o DIR` — output directory (default: `dataset/`)

## Seed reproducibility

Every accepted sample is reproducible from stored metadata (seed + template +
parameters). Use the same `--seed` across stages for consistency or vary it to
generate different parameter samples.

## Cache strategy

Simulation results are cached to avoid re-running Xyce on the same netlist.
Use `--cache-dir` to specify a persistent cache directory, or `--no-cache` to
skip caching entirely.

## Visual checks (opt-in)

Vision-model quality checks run locally via Ollama. The `--visual` flag on
`eqa validate` invokes two checks:
- `topology_match` — VLM verifies the schematic matches the stated topology
- `label_visibility` — VLM checks component labels are readable

### Setup

```bash
# 1. Install Ollama (one-time)
brew install ollama       # macOS
# or download from https://ollama.com

# 2. Start the service (runs on localhost:11434)
ollama serve

# 3. Pull the vision model (~4 GB, one-time)
ollama pull deepseek-vl2-tiny
```

Configuration (in `.env`, defaults shown):

```env
VISION_BASE_URL=http://localhost:11434/v1
VISION_MODEL=deepseek-vl2-tiny
```

When Ollama is not running or the model is not pulled, vision checks
return PASS silently — they are advisory (WARN), never blocking.

## Behavioral guidance

When the user asks to **validate** or **run the pipeline** (including
`--verify` on `eqa questions`), and they have not explicitly mentioned
`--visual`:

1. Always ask: **"Would you also like to run visual checks on the
   schematics? This uses a local Ollama instance with deepseek-vl2-tiny.
   You'll need Ollama installed with `ollama serve` running and the model
   pulled (`ollama pull deepseek-vl2-tiny`)."**
2. If the user says yes, add `--visual` to the validate command.
3. If the user says no or is unsure, proceed without `--visual`.

Do NOT ask this when:
- The user has already specified `--visual` (explicit intent)
- The user is only asking about emit, simulate, or questions without
  validation

## Implementation notes

- Always run `uv sync` before first use to install dependencies plus extras:
  ```bash
  uv sync --extra sim --extra data --extra render
  ```
- Simulation requires Xyce to be installed and on PATH.
- Check project health with `uv run ruff check .` and `uv run pytest` after
  changes.

## Troubleshooting

| Problem | Likely fix |
|---------|-----------|
| Xyce not found | Install Xyce or ensure it's on PATH |
| Import errors | Run `uv sync --extra sim --extra data --extra render` |
| No templates listed | Check `src/electronics_qa_generator/templates/` for registered topologies |
| Output directory issues | Use absolute paths or create the directory first |
