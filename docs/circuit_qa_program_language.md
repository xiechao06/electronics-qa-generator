# Circuit QA Functional-Program DSL

This document describes a small **domain-specific language (DSL)** for representing electronics question-answer items as **executable reasoning programs**.

The design is inspired by CLEVR:

> A question should not exist only as text. It should also have a machine-readable program that precisely describes how the answer is computed.

In this DSL:
- the **question text** is the human-facing form
- the **program** is the executable semantic form
- the **answer** is computed from simulation-backed data

---

## 1. Goals

The DSL should:

- be **deterministic**
- be **executable** over stored simulation results and metadata
- support **reasoning decomposition** into explicit steps
- make question types easy to classify and balance
- support **verification** of every answer
- work across common circuit analyses: `.op`, `.dc`, `.ac`, `.tran`

---

## 2. Core idea

A QA item has three layers:

1. **Natural question**
2. **Program**
3. **Answer**

Example:

### Question
> What is the approximate -3 dB cutoff frequency of this circuit?

### Program
```json
[
  {"op": "load_analysis", "analysis": "ac"},
  {"op": "get_trace", "trace": "V(out)"},
  {"op": "estimate_low_freq_gain"},
  {"op": "find_cutoff_db", "drop_db": 3}
]
```

### Answer
```json
{
  "value": 1591.5,
  "unit": "Hz",
  "text": "1.59 kHz"
}
```

So the DSL is the hidden reasoning process.

---

## 3. Execution model

A program is a sequence of operations executed left to right.

Each operation:
- consumes the current context
- may read simulation data or metadata
- may store intermediate values
- returns an updated context

Think of execution as:

```text
sample data + program -> intermediate states -> final answer
```

The execution context may contain:
- loaded analysis data
- active trace
- scalar values
- sets of nodes/components
- variant samples
- intermediate measurements
- comparison results

---

## 4. Data model assumed by the DSL

The DSL assumes each sample contains a structured record with fields like:

```json
{
  "id": "rc_lowpass_0001",
  "topology": "rc_lowpass",
  "parameters": {"R1": 10000, "C1": 1e-8},
  "analyses": {
    "op": {...},
    "dc": {...},
    "ac": {...},
    "tran": {...}
  },
  "facts": {...},
  "variants": {
    "base": {...},
    "double_C1": {...}
  }
}
```

The DSL can operate either:
- directly on raw traces, or
- on precomputed fact tables, or
- on both

---

## 5. Program representation

The simplest representation is a JSON array of operations.

Each operation is an object:

```json
{"op": "operation_name", "arg1": "...", "arg2": 123}
```

Example:

```json
[
  {"op": "load_analysis", "analysis": "tran"},
  {"op": "get_trace", "trace": "V(out)"},
  {"op": "compute_peak_to_peak"}
]
```

This design is:
- easy to serialize
- easy to validate
- easy to execute
- easy to inspect in a dataset

---

## 6. DSL operation categories

A good first version of the DSL can be divided into six categories.

### A. Sample and analysis access
These operations select which sample, variant, or analysis to use.

### B. Trace and entity selection
These operations choose a node, branch, trace, component, or parameter.

### C. Measurement operators
These compute numeric quantities from traces or scalar analysis outputs.

### D. Classification operators
These map data to labels like low-pass/high-pass or clipped/not-clipped.

### E. Comparison and logic operators
These compare values, counts, or labels.

### F. Formatting and answer operators
These normalize units or produce final answer text.

---

## 7. Core operation set

Below is a practical starter set.

---

## 7.1 Sample and analysis access ops

### `load_sample`
Load a named sample or variant.

```json
{"op": "load_sample", "sample": "base"}
```

### `load_variant`
Load a specific counterfactual or perturbed version.

```json
{"op": "load_variant", "variant": "double_C1"}
```

### `load_analysis`
Select one analysis result.

```json
{"op": "load_analysis", "analysis": "ac"}
```

Allowed values might include:
- `op`
- `dc`
- `ac`
- `tran`

---

## 7.2 Trace and entity selection ops

### `get_trace`
Select a trace by name.

```json
{"op": "get_trace", "trace": "V(out)"}
```

### `get_node_voltage`
Get a scalar node voltage, usually from `.op`.

```json
{"op": "get_node_voltage", "node": "out"}
```

### `get_branch_current`
Get branch current for a component or source.

```json
{"op": "get_branch_current", "element": "R1"}
```

### `get_parameter`
Read a parameter value from sample metadata.

```json
{"op": "get_parameter", "name": "R1"}
```

### `get_component_type`
Return the type of a named component.

```json
{"op": "get_component_type", "element": "Q1"}
```

### `select_output_node`
Use the canonical output node if defined in metadata.

```json
{"op": "select_output_node"}
```

---

## 7.3 Measurement ops

### `measure_at_time`
Measure the current trace at a specified time.

```json
{"op": "measure_at_time", "time_s": 0.001}
```

### `measure_at_freq`
Measure the current trace at a specified frequency.

```json
{"op": "measure_at_freq", "freq_hz": 1000}
```

### `measure_at_dc_input`
Measure the trace at a specified DC sweep input value.

```json
{"op": "measure_at_dc_input", "input_value": 2.5}
```

### `compute_max`
Return max value of current trace.

```json
{"op": "compute_max"}
```

### `compute_min`
Return min value of current trace.

```json
{"op": "compute_min"}
```

### `compute_peak_to_peak`
Return max - min.

```json
{"op": "compute_peak_to_peak"}
```

### `compute_average`
Average over trace or selected interval.

```json
{"op": "compute_average"}
```

### `compute_rms`
Compute RMS value.

```json
{"op": "compute_rms"}
```

### `estimate_steady_state`
Estimate steady-state value from a transient waveform.

```json
{"op": "estimate_steady_state"}
```

### `compute_rise_time`
Measure rise time using configured thresholds.

```json
{"op": "compute_rise_time", "low_frac": 0.1, "high_frac": 0.9}
```

### `compute_settling_time`
Measure time to remain within a tolerance band.

```json
{"op": "compute_settling_time", "tol_frac": 0.02}
```

### `compute_overshoot_percent`
Compute overshoot relative to steady-state target.

```json
{"op": "compute_overshoot_percent"}
```

### `estimate_low_freq_gain`
Estimate low-frequency gain from AC response.

```json
{"op": "estimate_low_freq_gain"}
```

### `estimate_high_freq_gain`
Estimate high-frequency gain from AC response.

```json
{"op": "estimate_high_freq_gain"}
```

### `find_cutoff_db`
Find frequency at which gain drops by specified dB.

```json
{"op": "find_cutoff_db", "drop_db": 3}
```

### `find_resonant_frequency`
Find peak magnitude frequency.

```json
{"op": "find_resonant_frequency"}
```

### `measure_phase_at_freq`
Read phase at a specified frequency.

```json
{"op": "measure_phase_at_freq", "freq_hz": 1000}
```

### `compute_ripple_pp`
Compute steady-state ripple peak-to-peak.

```json
{"op": "compute_ripple_pp", "window": "last_cycle"}
```

---

## 7.4 Classification ops

### `classify_response_type`
Classify AC response.

```json
{"op": "classify_response_type"}
```

Possible outputs:
- `low_pass`
- `high_pass`
- `band_pass`
- `band_stop`
- `flat`
- `other`

### `detect_clipping`
Determine whether waveform is clipped.

```json
{"op": "detect_clipping"}
```

### `classify_monotonicity`
Classify whether a DC sweep is increasing, decreasing, or non-monotonic.

```json
{"op": "classify_monotonicity"}
```

### `classify_transient_damping`
Classify waveform as underdamped, overdamped, critically damped, etc.

```json
{"op": "classify_transient_damping"}
```

### `classify_operating_region`
Classify transistor operating region if inferable.

```json
{"op": "classify_operating_region", "element": "Q1"}
```

---

## 7.5 Comparison and logic ops

### `save_as`
Store current result under a variable name.

```json
{"op": "save_as", "name": "f_base"}
```

### `load_var`
Load previously stored variable.

```json
{"op": "load_var", "name": "f_base"}
```

### `compare_values`
Compare two variables numerically.

```json
{"op": "compare_values", "a": "f_variant", "b": "f_base", "mode": "direction"}
```

Modes might include:
- `greater_than`
- `less_than`
- `equal_with_tolerance`
- `direction`
- `difference`
- `ratio`

### `compare_labels`
Compare two categorical labels.

```json
{"op": "compare_labels", "a": "resp1", "b": "resp2"}
```

### `greater_than`
Boolean comparison.

```json
{"op": "greater_than", "a": "gain1", "b": "gain2"}
```

### `less_than`
Boolean comparison.

```json
{"op": "less_than", "a": "v1", "b": "v2"}
```

### `equal_with_tolerance`
Numeric equality test.

```json
{"op": "equal_with_tolerance", "a": "x", "b": "y", "abs_tol": 0.01}
```

### `exists`
Whether a set or condition is non-empty.

```json
{"op": "exists", "name": "crossing_points"}
```

---

## 7.6 Formatting and answer ops

### `convert_unit`
Convert to a display unit.

```json
{"op": "convert_unit", "unit": "kHz"}
```

### `round_sigfig`
Round to significant figures.

```json
{"op": "round_sigfig", "n": 3}
```

### `emit_answer`
Mark the current value as final answer.

```json
{"op": "emit_answer"}
```

### `emit_mcq_answer`
Emit a choice label instead of raw scalar.

```json
{"op": "emit_mcq_answer", "choice": "B"}
```

---

## 8. Example programs by question type

---

## 8.1 Direct numeric question

### Question
> What is the DC output voltage at node out?

### Program
```json
[
  {"op": "load_analysis", "analysis": "op"},
  {"op": "get_node_voltage", "node": "out"},
  {"op": "convert_unit", "unit": "V"},
  {"op": "round_sigfig", "n": 3},
  {"op": "emit_answer"}
]
```

---

## 8.2 Derived numeric question

### Question
> What is the approximate -3 dB cutoff frequency of this circuit?

### Program
```json
[
  {"op": "load_analysis", "analysis": "ac"},
  {"op": "get_trace", "trace": "V(out)"},
  {"op": "estimate_low_freq_gain"},
  {"op": "find_cutoff_db", "drop_db": 3},
  {"op": "convert_unit", "unit": "kHz"},
  {"op": "round_sigfig", "n": 3},
  {"op": "emit_answer"}
]
```

---

## 8.3 Classification question

### Question
> What type of filter response does this circuit exhibit?

### Program
```json
[
  {"op": "load_analysis", "analysis": "ac"},
  {"op": "get_trace", "trace": "V(out)"},
  {"op": "classify_response_type"},
  {"op": "emit_answer"}
]
```

---

## 8.4 Comparison question

### Question
> If C1 is doubled, does the cutoff frequency increase or decrease?

### Program
```json
[
  {"op": "load_sample", "sample": "base"},
  {"op": "load_analysis", "analysis": "ac"},
  {"op": "get_trace", "trace": "V(out)"},
  {"op": "estimate_low_freq_gain"},
  {"op": "find_cutoff_db", "drop_db": 3},
  {"op": "save_as", "name": "f_base"},

  {"op": "load_variant", "variant": "double_C1"},
  {"op": "load_analysis", "analysis": "ac"},
  {"op": "get_trace", "trace": "V(out)"},
  {"op": "estimate_low_freq_gain"},
  {"op": "find_cutoff_db", "drop_db": 3},
  {"op": "save_as", "name": "f_variant"},

  {"op": "compare_values", "a": "f_variant", "b": "f_base", "mode": "direction"},
  {"op": "emit_answer"}
]
```

---

## 8.5 Transient waveform question

### Question
> What is the peak-to-peak ripple voltage at the output?

### Program
```json
[
  {"op": "load_analysis", "analysis": "tran"},
  {"op": "get_trace", "trace": "V(out)"},
  {"op": "compute_ripple_pp", "window": "last_cycle"},
  {"op": "convert_unit", "unit": "V"},
  {"op": "round_sigfig", "n": 3},
  {"op": "emit_answer"}
]
```

---

## 9. Optional higher-level derived ops

To keep programs short, some compound operations may be useful.

### `measure_cutoff`
Equivalent to:
- load AC trace
- estimate low-frequency gain
- find -3 dB crossing

### `measure_gain_db`
Equivalent to:
- select AC trace
- measure magnitude at frequency
- convert to dB if needed

### `measure_steady_state_voltage`
Equivalent to:
- select transient output
- estimate steady-state

These are convenient, but they hide reasoning steps.

Recommendation:
- store both the **expanded program** and the **compact alias** if possible

---

## 10. Type system

Each op should have input/output types for validation.

Example types:
- `sample`
- `analysis`
- `trace`
- `scalar`
- `frequency`
- `time`
- `label`
- `boolean`
- `set`
- `comparison_result`

Example typing rule:

- `get_trace` requires current context to contain selected analysis
- `find_cutoff_db` requires current context to contain AC magnitude trace
- `convert_unit` requires current value to be scalar with compatible dimension

This makes malformed programs easier to catch.

---

## 11. Validation rules

The DSL should support static and runtime validation.

### Static validation
- op name is known
- required args are present
- arg types are valid
- operation order is legal

### Runtime validation
- requested trace exists
- requested frequency is in range
- cutoff crossing actually exists
- comparison variables are defined
- units are compatible

If validation fails, the QA item should be rejected or regenerated.

---

## 12. How this supports dataset analysis

Because every question has a program, you can label items by:
- number of steps
- analysis type used
- required reasoning family
- whether comparison is involved
- whether counterfactual simulation is involved
- whether trace reading or symbolic fact lookup is involved

For example:

```json
{
  "reasoning_tags": [
    "ac_analysis",
    "derived_numeric",
    "multi_step",
    "feature_extraction"
  ],
  "program_length": 4
}
```

This is valuable for benchmark diagnostics.

---

## 13. How the DSL fits with the LLM

The DSL is the truth-bearing layer.

Recommended separation:

- **DSL + code + simulator** compute the answer
- **LLM** only rephrases or explains

Example:

```text
DSL program -> answer value -> natural-language question rewrite by LLM
```

The LLM should never replace the program.

---

## 14. Minimal QA item schema using the DSL

```json
{
  "id": "qa_0001",
  "question": "What is the approximate -3 dB cutoff frequency of this circuit?",
  "program": [
    {"op": "load_analysis", "analysis": "ac"},
    {"op": "get_trace", "trace": "V(out)"},
    {"op": "estimate_low_freq_gain"},
    {"op": "find_cutoff_db", "drop_db": 3},
    {"op": "convert_unit", "unit": "kHz"},
    {"op": "round_sigfig", "n": 3},
    {"op": "emit_answer"}
  ],
  "answer": {
    "value": 1.59,
    "unit": "kHz",
    "text": "1.59 kHz"
  },
  "reasoning_tags": ["ac_analysis", "derived_numeric", "feature_extraction"]
}
```

---

## 15. Recommended first version

For an MVP, implement only these ops first:

- `load_sample`
- `load_analysis`
- `get_trace`
- `get_node_voltage`
- `measure_at_freq`
- `compute_max`
- `compute_min`
- `compute_peak_to_peak`
- `estimate_steady_state`
- `estimate_low_freq_gain`
- `find_cutoff_db`
- `classify_response_type`
- `save_as`
- `compare_values`
- `convert_unit`
- `round_sigfig`
- `emit_answer`

This is enough for:
- direct numeric
- derived numeric
- classification
- comparison
- transient ripple questions

---

## 16. Bottom line

A **functional-program DSL** for circuit QA is a small executable language that represents the hidden reasoning steps behind each question.

In one sentence:

> **The question text is for humans; the DSL program is the authoritative machine-readable computation of the answer.**

That makes the dataset:
- more rigorous
- easier to verify
- easier to analyze
- more CLEVR-like in spirit
