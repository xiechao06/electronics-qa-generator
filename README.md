# electronics-qa-generator

A pipeline for generating **multimodal electronics circuit Q/A items** with
**simulator-grounded ground-truth answers**, targeting an
[MMMU](https://mmmu-benchmark.github.io/)-style benchmark for the Electronics
subfield.

The design is inspired by two papers:

- **CLEVR** — every question carries a machine-readable program, so answers are
  *programmatically guaranteed* rather than guessed.
- **AutoCkt** — SPICE is the source of truth; circuits and measurements come from
  a real simulator in the loop, not from an LLM.

> **Core principle:** Simulation establishes facts → code derives answers → the
> LLM only expresses or reviews truth that has already been computed. The LLM is
> never the source of numerical truth.

See [`docs/plan.md`](docs/plan.md) and [`docs/architecture.md`](docs/architecture.md)
for the full design, and [`docs/circuit_qa_program_language.md`](docs/circuit_qa_program_language.md)
for the CLEVR-style DSL.

## Status

Early scaffolding. The package layout and pipeline stages are stubbed out and
will be implemented step by step. Nothing generates real data yet.

## Pipeline

```
templates → sampling → netlist → simulation (Xyce) → parsing → extraction
  → questions (+ optional llm) → validation → rendering → output
```

| Stage | Package | Responsibility |
|-------|---------|----------------|
| Template library | `templates/` | Circuit families, topologies, parameter ranges, rejection rules |
| Sampler | `sampling/` | Constrained randomization of values, stimuli, loads, variants |
| Netlist generator | `netlist/` | Emit deterministic Xyce/SPICE netlists |
| Simulation orchestrator | `simulation/` | Run Xyce (.op/.dc/.ac/.tran), batching, retries, caching |
| Result parser | `parsing/` | Raw outputs → structured arrays/tables |
| Fact extractor | `extraction/` | Canonical ground-truth fact table |
| Question engine | `questions/` | Question types + deterministic answers + CLEVR-style programs |
| Optional LLM layer | `llm/` | Paraphrase / explanations / distractor wording / tags |
| Verifier & filters | `validation/` | Answer consistency, ambiguity, quality, leakage/split checks |
| Renderer | `rendering/` | Schematics, waveform/Bode plots, tables |
| Dataset assembler | `output/` | JSONL/Parquet export + train/val/test splits |

## Requirements

- **Python 3.14** (pinned via `.python-version`)
- [`uv`](https://docs.astral.sh/uv/) for environment and build management
- **Xyce** (external SPICE simulator) — required once the simulation stage is
  implemented; install separately.

## Getting started

```bash
# Create the environment and install the project (dev tools included)
uv sync

# Run the CLI
uv run eqa --help
uv run eqa generate -n 10 -o dataset

# Run tests / lint
uv run pytest
uv run ruff check .
```

Optional dependency groups (pull in as you implement stages):

```bash
uv sync --extra sim     # numpy, scipy
uv sync --extra data    # pyarrow, pandas
uv sync --extra render  # matplotlib
```

## Reference data

The repo includes a copy of the MMMU Electronics subset for reference and to
mirror the target schema:

- `mmmu_electronics/` — original parquet splits (dev/validation/test)
- `mmmu_electronics_unpacked/` — JSONL/CSV + extracted images
- `unpack_mmmu_electronics.py` — script that produced the unpacked form

## Layout

```
src/electronics_qa_generator/   # the package (one subpackage per pipeline stage)
  models.py                     # shared dataclasses (CircuitRecord, QAItem, Sample)
  pipeline.py                   # end-to-end orchestration skeleton
  cli.py                        # `eqa` console script
docs/                           # design docs and paper explainers
tests/                          # smoke tests
```

## License

TBD.

## LLM humanization (optional)

The `eqa questions` command accepts an opt-in `--humanize` flag that rewrites
questions in natural, exam-style language and generates optional explanations
via a DeepSeek LLM (`deepseek-v4-pro`). Answers, values, units, and programs
are **never** altered by the LLM — humanization runs strictly after the
deterministic answer is fixed.

### Setup

Create a `.env` file in the project root:

```env
DEEPSEEK_API_KEY=sk-your-key-here
# Optional overrides:
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# DEEPSEEK_MODEL=deepseek-v4-pro
```

> The `.env` file is `.gitignore`d. No Python package is needed — keys are
> read with the stdlib only.

### Usage

```bash
# Normal run (no LLM calls)
eq questions voltage_divider --seed 42

# With humanization
eq questions voltage_divider --seed 42 --humanize
```

When no key is configured (or the API is unreachable), `--humanize` falls back
silently to the original templated questions. Tests use a fake provider and
never touch the network.
