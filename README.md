# electronics-qa-generator

A pipeline that generates **multimodal electronics circuit Q/A items** with
**SPICE/Xyce-grounded ground-truth answers**, targeting an
[MMMU](https://mmmu-benchmark.github.io/)-style benchmark for the Electronics
subfield.

Inspired by **CLEVR** (questions backed by executable programs) and **AutoCkt**
(simulator-in-the-loop as source of truth).

> **Core principle:** Simulation establishes facts → code derives answers →
> the LLM only paraphrases or reviews truth that has already been computed.
> The LLM is never the source of numerical truth.

See [`docs/plan.md`](docs/plan.md), [`docs/architecture.md`](docs/architecture.md),
and [`AGENTS.md`](AGENTS.md) for the full design and pipeline commands.

## Quick start

```bash
git clone https://github.com/xiechao06/electronics-qa-generator
cd electronics-qa-generator
```

Then prompt a coding agent:

> *"Generate roughly 10,000 Q/A pairs."*

The agent reads `AGENTS.md`, runs the pipeline, and produces JSONL output
with schematics. No manual setup beyond `uv sync`.

To run directly:

```bash
uv sync --extra sim --extra data --extra render

# Small batch (200 items, ~1 second):
uv run python scripts/batch_generate.py --total 200 --workers 4 -o output/batch

# Large batch (100k items, ~2 minutes):
uv run python scripts/batch_generate.py --total 100000 --workers 8 -o output/batch
```

## What it produces

| Artifact | Location |
|---|---|
| QA items (JSONL) | `output/batch/qa_items.jsonl` |
| Schematics (PNG) | `output/batch/images/<topology>/<seed>.png` |

Each QA item includes a `schematic_path`, `question`, `answer`, `answer_value`,
`unit`, `tolerance`, `question_type`, and a `program` (CLEVR-style instruction
sequence).

## Available topologies (14)

```
voltage_divider     rc_lowpass          rc_highpass         rlc_bandpass
half_wave_rectifier rc_step_response    rl_step_response    ac_phasor_rc
bjt_ce_amplifier    bjt_emitter_follower mosfet_cs_amplifier resistor_network
op_amp_inverting    rlc_series_resonance
```

## Question types

| Type | Example |
|---|---|
| `direct` | Determine the −3 dB cutoff frequency |
| `derived` | Compute the quality factor Q = f₀ / BW |
| `classification` | Classify this filter as low-pass, high-pass, or band-pass |
| `comparison` | Is V(out) greater than half of V(in)? |

All answers are computed deterministically from Xyce simulation facts
(`.op`, `.ac`, `.tran`) via a CLEVR-style program engine. Questions
use hand-written humanized templates — no LLM involved in truth creation.

## Requirements

- **Python 3.14** (pinned via `.python-version`)
- [`uv`](https://docs.astral.sh/uv/) for environment management
- **Xyce** SPICE simulator on PATH

## CLI pipeline

```
emit → simulate → questions → validate → assemble
```

| Command | What it does |
|---|---|
| `uv run eqa emit <topology> --seed N --render` | Sample template, emit netlist + schematic |
| `uv run eqa simulate <topology> --seed N` | Run Xyce, extract facts |
| `uv run eqa questions <topology> --seed N` | Generate Q/A items from facts |
| `uv run eqa validate <topology> --seed N` | Static checks on QA items |
| `uv run eqa assemble -o dataset` | Assemble MMMU-compatible dataset |

For batch generation across many seeds, use `scripts/batch_generate.py`.

## Visual checks (opt-in)

`eqa validate --visual` runs a local Ollama VLM to verify schematics:

```bash
brew install ollama
ollama serve
ollama pull deepseek-vl2-tiny
```

`.env` defaults:
```env
VISION_BASE_URL=http://localhost:11434/v1
VISION_MODEL=deepseek-vl2-tiny
```

## Reference data

- `mmmu_electronics/` — original MMMU Electronics parquet splits
- `mmmu_electronics_unpacked/` — JSONL/CSV + extracted images

Treat these as read-only target schema references.

## Layout

```
src/electronics_qa_generator/   # package, one subpackage per pipeline stage
  models.py                     # CircuitRecord, QAItem, Sample
  questions/templates.py        # hand-written humanized question templates
  render/svg/                   # SVG layout templates per topology
  graph/                        # circuit graph model
  simulation/                   # Xyce runner, fact cache
  extraction/                   # fact extractors per topology
  validation/                   # static + LLM + visual checks
  output/                       # dataset assembler
scripts/
  batch_generate.py             # high-throughput batch generation
docs/                           # design docs and paper explainers
tests/                          # pytest suite
```

## License

TBD.
