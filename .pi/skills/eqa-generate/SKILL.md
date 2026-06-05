---
name: eqa-generate
description: Generate multimodal electronics circuit Q/A items with SPICE/Xyce-grounded ground-truth answers. Runs the full pipeline: sampling → netlist → simulation → parsing → extraction → questions → rendering → assembly. Use when asked to generate QA items, create benchmark datasets, produce circuit questions, or run the electronics QA pipeline.
---

# Electronics QA Generator

Runs the full `electronics-qa-generator` pipeline to produce MMMU-compatible
question/answer pairs with SPICE/Xyce-grounded answers and schematic images.

## Prerequisites

- Python 3.14 via `uv`
- Xyce on PATH (for SPICE simulation)
- `uv sync --extra render` for schematic images
- (Optional) Ollama with `deepseek-vl2-tiny` for visual verification
- (Optional) `.env` file with `DEEPSEEK_API_KEY` for LLM humanization

```bash
uv sync --extra render
```

## Quick start

Generate a complete dataset with all 5 circuit topologies:

```bash
uv run eqa assemble --seed 42 --out benchmarks/v1
```

This produces:
```
benchmarks/v1/
├── dataset.jsonl       # 25 MMMU-compatible QA items
├── images/             # 5 schematic PNGs
└── report.json         # validation summary
```

## Usage patterns

### Generate one topology

```bash
uv run eqa questions rc_lowpass --seed 42
```

### List available topologies

```bash
uv run eqa questions --list
```

Output:
```
half_wave_rectifier: 5 question template(s)
rc_highpass: 5 question template(s)
rc_lowpass: 5 question template(s)
rlc_bandpass: 5 question template(s)
voltage_divider: 5 question template(s)
```

### Generate with verification

```bash
uv run eqa validate rc_lowpass --seed 42
uv run eqa validate rc_lowpass --seed 42 --json  # CI-friendly JSON output
```

### Generate with LLM humanization

```bash
# Requires DEEPSEEK_API_KEY in .env
uv run eqa questions rc_lowpass --seed 42 --humanize
```

### Regenerate with different seed

```bash
uv run eqa assemble --seed 123 --out benchmarks/v2
```

### Use fact cache for speed

```bash
uv run eqa assemble --seed 42 --cache-dir .cache/eqa
```

## Topologies and question types

| Topology | Simulation | Questions | Example answer |
|---|---|---|---|
| `voltage_divider` | `.op` | 5 | "7.586 V" |
| `rc_lowpass` | `.ac` | 5 | "233 Hz" |
| `rc_highpass` | `.ac` | 5 | "235 Hz" |
| `rlc_bandpass` | `.ac` | 5 | "6026 Hz" |
| `half_wave_rectifier` | `.tran` | 5 | "5.480 V" |

Each topology has 5 question types: direct, derived, classification, comparison,
plus topology-specific variants.

## Output format (MMMU-compatible JSONL)

```json
{"id": "rc_lowpass_0000002a_0", "question": "Find the −3 dB cutoff...", "answer": "233.496 Hz"}
{"id": "rc_lowpass_0000002a_3", "question": "Classify the frequency response...", "answer": "low-pass", "options": "[\"low-pass\", \"high-pass\", \"band-pass\"]", "image": "images/rc_lowpass_0000002a.png"}
```

## Troubleshooting

### Xyce not found
Install from https://xyce.sandia.gov/ and ensure `Xyce` is on PATH.

### Simulation doesn't converge
The pipeline retries with ±5% resistor perturbation. If it still fails,
try a different seed or verify Xyce installation.

### Matplotlib not installed
```bash
uv sync --extra render
```

### DeepSeek API key not configured
Create `.env` in project root:
```env
DEEPSEEK_API_KEY=sk-your-key
```
