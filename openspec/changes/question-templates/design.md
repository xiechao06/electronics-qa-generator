## Context

Five templates exist with known fact schemas. `QAItem` is defined in `models.py` with fields: `question_type`, `question`, `answer`, `answer_value`, `unit`, `tolerance`, `choices`, `program`, `explanation`. The pipeline currently stops at fact extraction. We need question generation that follows the CLEVR principle: every answer is deterministically computable from facts, and every question carries a machine-readable program showing how.

## Goals / Non-Goals

**Goals:**
- 2–4 question templates per of the 5 circuit topologies (10–20 total)
- Four question types: direct, derived, classification, comparison
- Each question produces a valid `QAItem` with answer, value, unit, tolerance, program
- CLEVR-style program representation using a small set of deterministic ops
- Registry mapping topology → list of question templates
- `eqa questions` CLI subcommand: full pipeline from template to QA items

**Non-Goals:**
- Multiple-choice distractors (LLM stage)
- Natural language paraphrasing (LLM stage)
- Counterfactual or "what-if" questions (future)
- Trend questions requiring multiple samples (future)

## Decisions

### 1. Question template structure

Each question template is a plain dict with six keys:

```python
{
    "id": "vd_direct_vout",          # unique within topology
    "question_type": "direct",       # type taxonomy
    "question_template": "...",      # with {param} placeholders
    "program": [...],                # CLEVR-style op list
    "answer_keys": ["Vout_dc"],      # which fact keys answer depends on
    "answer_formatter": "numeric",   # how to format the answer
}
```

The `question_template` string uses Python `.format()` syntax with placeholders like `{Vout_dc}`, `{Vin_dc}`, `{R1_ohm}` drawn from the merged facts + parameters dict.

### 2. Question type taxonomy

| Type | Description | Example |
|---|---|---|
| `direct` | Read a single fact value | "What is the DC output voltage?" |
| `derived` | Compute from multiple facts | "What is the voltage divider ratio Vout/Vin?" |
| `classification` | Pick a label from a fact | "Is this a low-pass, high-pass, or band-pass filter?" |
| `comparison` | Compare a fact to a reference | "Is the cutoff frequency above or below 1 kHz?" |

### 3. CLEVR-style program representation

Each question carries a `program` — an ordered list of deterministic ops:

```python
# Direct: "What is Vout_dc?"
[
    {"op": "read_fact", "fact": "Vout_dc"},
    {"op": "format_numeric", "value": "$0", "unit": "V", "precision": 3},
]

# Derived: "What is the divider ratio?"
[
    {"op": "read_fact", "fact": "Vout_dc"},
    {"op": "read_fact", "fact": "Vin_dc"},
    {"op": "div", "a": "$0", "b": "$1"},
    {"op": "format_numeric", "value": "$2", "unit": None, "precision": 4},
]

# Classification: "Is this a low-pass or high-pass filter?"
[
    {"op": "read_fact", "fact": "behavior"},
    {"op": "classify", "value": "$0", "labels": ["low-pass", "high-pass", "band-pass", "none"]},
]

# Comparison: "Is cutoff > 1 kHz?"
[
    {"op": "read_fact", "fact": "cutoff_hz"},
    {"op": "compare", "a": "$0", "b": 1000.0, "op": ">"},
    {"op": "return_bool", "value": "$1", "true_label": "yes", "false_label": "no"},
]
```

Ops available: `read_fact`, `read_param`, `add`, `sub`, `mul`, `div`, `abs`, `compare`, `classify`, `format_numeric`, `return_bool`, `return_label`, `return_value`.

### 4. Answer computation

Answers are computed at generation time from the program + facts + params:

```python
def compute_answer(program: list[dict], facts: dict, params: dict) -> tuple:
    """Return (answer_value: float|None, answer_text: str, unit: str|None, tolerance: float|None)."""
```

The computation walks the program, evaluating each op. `read_fact` fetches from facts dict. `read_param` fetches from params. Numeric ops compute. `format_numeric` produces the `(value, unit, tolerance)` triple. `classify` returns the label string.

Tolerance is derived from the last `format_numeric` precision: `tolerance = 0.5 * 10^{-precision}` for numeric answers, `None` for classification.

### 5. Per-template question allocation

| Topology | Direct | Derived | Classification | Comparison |
|---|---|---|---|---|
| `voltage_divider` | Vout_dc | divider_ratio | — | Vout vs Vin/2 |
| `rc_lowpass` | cutoff_hz | — | behavior (low-pass) | cutoff vs reference |
| `rc_highpass` | cutoff_hz | — | behavior (high-pass) | cutoff vs reference |
| `rlc_bandpass` | center_freq_hz | Q factor | behavior (band-pass) | bandwidth vs center/10 |
| `half_wave_rectifier` | Vout_dc | ripple ratio | — | ripple vs threshold |

This gives **16 question templates total**.

### 6. Answer format and precision

- Direct numeric: value with 3 significant figures, unit from a unit map
- Derived: 4 significant figures (computed → more precision needed)
- Classification: label string, no unit, no tolerance
- Comparison: boolean or yes/no, no unit, no tolerance

Unit map:
```python
_UNITS = {
    "Vout_dc": "V", "Vin_dc": "V", "Vout_peak": "V",
    "cutoff_hz": "Hz", "center_freq_hz": "Hz", "bandwidth_hz": "Hz",
    "passband_gain_db": "dB", "peak_gain_db": "dB",
    "divider_ratio": None, "Q": None, "ripple_vpp": "V",
    "behavior": None,
}
```

### 7. Question type `multiple-choice` in QAItem

When a classification or comparison question is generated, `choices` is populated:
- Classification: list of possible labels
- Comparison: `["yes", "no"]` or `["above", "below"]`

For direct/derived questions, `choices` is `None` (open-ended numeric answer).

### 8. CLI: `eqa questions`

```
eqa questions <topology> [--seed N] [--cache-dir DIR] [--no-cache] [--jsonl]
```

Behavior:
- Sample template, run Xyce (or use cache), extract facts
- Generate all question templates for that topology
- Compute answers deterministically from facts + params
- Print JSON array of QAItem objects to stdout
- `--jsonl` flag: one JSON object per line instead of array

Also: `eqa questions --list` to list topologies with question counts.

## Risks / Trade-offs

- **[Risk] Program interpreter is overengineered for MVP** → We implement `compute_answer` as a simple 20-line interpreter; the program format is documentation for humans and potential future LLM training, not a general-purpose runtime.
- **[Trade-off] Only open-ended answers, no distractors** → No multiple-choice items with wrong-answer distractors in this change. Those require the LLM stage (future) to generate plausible wrong answers.
- **[Risk] Comparison questions need reference values** → References are hardcoded per topology (e.g., "1 kHz" for RC low-pass). Future: sample reference from interesting points (e.g., actual cutoff × 2).
