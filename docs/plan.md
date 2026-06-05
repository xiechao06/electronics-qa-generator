# Plan: Generating a Ground-Truth Electronics Q/A Dataset with Xyce

You want to build a dataset like MMMU, but for electronics/circuits, using a SPICE simulator such as Xyce. Your proposed pipeline is:

1. Generate many circuits.
2. Run simulations.
3. Generate ground-truth Q/A pairs from the simulation results.

This is a strong idea. The most important design principle is:

> Do not generate circuits or questions purely with an LLM. Use programmatic circuit templates, simulator outputs, and deterministic answer extraction. LLMs can help phrase questions, but the answers should come from code and simulation.

---

## 1. How to generate circuits

Do not start with fully random netlists. Fully random circuits often produce invalid, boring, unstable, or physically meaningless cases.

Instead, use a **template-based circuit generator**.

Each generated example should come from:

```text
circuit family
+ topology template
+ sampled component values
+ input stimulus
+ simulation type
+ measurement targets
```

For example:

```text
Family: RC filter
Template: first-order low-pass
Parameters: R = 10 kΩ, C = 10 nF
Input: AC source, 1 V amplitude
Simulation: AC sweep from 10 Hz to 10 MHz
Measurements: cutoff frequency, gain at 1 kHz, phase at 10 kHz
```

---

### 1.1 Start with circuit families

Begin with controlled families such as:

#### Passive circuits

- voltage divider
- current divider
- resistor ladder
- RC low-pass filter
- RC high-pass filter
- RLC band-pass filter
- RLC resonant circuit
- bridge circuit

#### Diode circuits

- half-wave rectifier
- full-wave bridge rectifier
- Zener regulator
- diode clipper
- diode clamper
- LED current-limiting circuit

#### Transistor circuits

- BJT common-emitter amplifier
- BJT emitter follower
- MOSFET common-source amplifier
- MOSFET switch
- differential pair

#### Op-amp circuits

- inverting amplifier
- non-inverting amplifier
- summing amplifier
- integrator
- differentiator
- active low-pass filter
- comparator

#### Mixed or harder circuits

- amplifier with load
- filter followed by amplifier
- rectifier plus smoothing capacitor
- regulator with load variation
- oscillator circuits

Start simple. Your first version could contain only:

```text
voltage divider
RC low-pass
RC high-pass
RLC band-pass
diode rectifier
op-amp amplifier
BJT common-emitter amplifier
```

That is already enough to generate many useful examples.

---

### 1.2 Represent each circuit as a parameterized template

Each template should define:

1. Components
2. Connectivity
3. Parameter ranges
4. Valid simulation types
5. Valid measurements
6. Rejection criteria

Example: RC low-pass filter.

```python
template = {
    "family": "rc_filter",
    "name": "rc_lowpass",
    "parameters": {
        "R": {"dist": "loguniform", "min": 1e3, "max": 1e6},
        "C": {"dist": "loguniform", "min": 1e-10, "max": 1e-6}
    },
    "simulation": {
        "type": "ac",
        "start_hz": 1,
        "stop_hz": 1e7,
        "points_per_decade": 50
    },
    "measurements": [
        "dc_gain",
        "cutoff_frequency",
        "gain_at_frequency",
        "phase_at_frequency"
    ]
}
```

Then your generator samples values:

```text
R = 18.2 kΩ
C = 4.7 nF
```

and emits a Xyce/SPICE netlist:

```spice
* RC low-pass filter
Vin in 0 AC 1
R1 in out 18.2k
C1 out 0 4.7n
.ac dec 50 1 10Meg
.print ac V(out)
.end
```

---

### 1.3 Use constrained randomization

You want randomness, but not chaos.

Good things to randomize:

- component values
- source amplitude
- source frequency
- load resistance
- supply voltage
- temperature
- transistor model
- simulation range
- which node is probed
- optional parasitic components

Bad things to randomize freely:

- arbitrary node connections
- arbitrary active device orientation
- arbitrary feedback loops
- arbitrary power supply placement

Those will produce many invalid circuits.

---

### 1.4 Add difficulty levels

A good dataset should have controlled difficulty.

#### Level 1: Simple canonical circuits

Examples:

- voltage divider
- first-order RC filter
- ideal op-amp amplifier
- diode rectifier

Questions are mostly direct.

Example:

> What is the DC output voltage?

#### Level 2: Parameter-varied circuits

Same topology, but broad parameter variation.

Example:

```text
R1, R2, C1, load resistance, source amplitude vary.
```

Questions require calculation or reading simulation results.

Example:

> What is the approximate -3 dB cutoff frequency?

#### Level 3: Perturbed circuits

Add non-ideal features:

- load resistor
- source resistance
- capacitor ESR
- diode forward voltage
- finite op-amp gain-bandwidth
- transistor bias variation

Example:

> Compared with the unloaded case, does the load resistor increase or decrease the output voltage?

#### Level 4: Composed circuits

Combine multiple blocks:

```text
RC filter + amplifier
rectifier + smoothing capacitor
divider + transistor switch
op-amp filter + load
```

Questions require multi-step reasoning.

Example:

> Which stage primarily determines the high-frequency roll-off?

---

### 1.5 Keep a structured circuit record

For every generated circuit, save more than the netlist.

Save a machine-readable record like:

```json
{
  "id": "rc_lowpass_000001",
  "family": "filter",
  "topology": "rc_lowpass",
  "parameters": {
    "R1": 18200,
    "C1": 4.7e-9
  },
  "netlist": "...",
  "simulation": {
    "type": "ac",
    "start_hz": 1,
    "stop_hz": 10000000
  },
  "probes": ["V(out)"],
  "expected_features": [
    "low_pass_behavior",
    "cutoff_frequency"
  ]
}
```

This record is crucial. It is the bridge between circuit generation, simulation, and Q/A generation.

---

## 2. Running simulations

Do not just save raw simulator output. Also save extracted features.

For each circuit, run Xyce and parse results into a feature table.

Example for an AC simulation:

```json
{
  "dc_gain_db": -0.01,
  "cutoff_frequency_hz": 1860.3,
  "gain_db_at_100hz": -0.02,
  "gain_db_at_1khz": -1.1,
  "gain_db_at_10khz": -14.8,
  "phase_deg_at_1khz": -28.4,
  "phase_deg_at_10khz": -79.5,
  "behavior": "low_pass"
}
```

Example for a transient simulation:

```json
{
  "steady_state_vout": 4.82,
  "rise_time_s": 0.00031,
  "settling_time_s": 0.0012,
  "overshoot_percent": 8.4,
  "peak_vout": 5.31,
  "min_vout": -0.02,
  "ripple_pp": 0.18
}
```

This extracted feature table is what you should use to generate answers.

---

## 3. How to generate Q/A pairs

The safest pipeline is:

```text
simulation result → feature extraction → fact table → question template → answer
```

The LLM may help produce natural language, but the answer should be computed by code.

---

### 3.1 Create a question taxonomy

Define question types before generating questions.

#### A. Direct value questions

These ask for a value directly measured from simulation.

Example:

> What is the output voltage at node `out` after the circuit reaches steady state?

Answer:

```text
4.82 V
```

Good for:

- DC simulations
- operating point analysis
- transient steady-state values
- current through a component
- voltage at a node

#### B. Derived value questions

These require post-processing simulation data.

Example:

> What is the approximate -3 dB cutoff frequency of the filter?

Answer:

```text
1.86 kHz
```

Other examples:

- peak-to-peak ripple
- rise time
- settling time
- resonance frequency
- bandwidth
- gain in dB
- phase shift
- power dissipation

#### C. Multiple-choice numerical questions

These are easier to evaluate and useful for benchmark datasets.

Example:

> What is the approximate cutoff frequency of the circuit?

A. 186 Hz  
B. 1.86 kHz  
C. 18.6 kHz  
D. 186 kHz

Correct answer:

```text
B
```

Distractors can be generated by scaling the correct answer:

```text
correct × 0.1
correct × 10
correct × 100
```

For electronics, this works well because order-of-magnitude errors are common.

#### D. Behavior classification questions

These ask what type of behavior the circuit shows.

Example:

> Based on the AC response, what type of filter is this circuit?

A. Low-pass  
B. High-pass  
C. Band-pass  
D. Band-stop

Answer:

```text
A. Low-pass
```

This can be generated from extracted response features.

#### E. Comparison questions

These are very useful if you simulate two variants.

Example:

> If the capacitance is doubled, what happens to the cutoff frequency?

Answer:

```text
It decreases.
```

But do not rely only on formulas. For ground truth, generate the modified circuit and re-run simulation.

You can store:

```json
{
  "original_cutoff_hz": 1860.3,
  "modified_cutoff_hz": 930.1,
  "relation": "decreases"
}
```

Then generate the question.

#### F. Trend questions

Use sweeps.

Example:

> As the input frequency increases from 100 Hz to 100 kHz, what happens to the output amplitude?

Answer:

```text
It decreases.
```

This is good for filters, amplifiers, rectifiers, and frequency-dependent circuits.

#### G. Fault or diagnosis questions

Generate a normal circuit and a faulty circuit.

Faults could include:

- resistor open
- capacitor short
- diode reversed
- transistor missing bias
- load too small
- wrong feedback resistor
- supply disconnected

Example:

> The output remains near 0 V for all input values. Which fault is most consistent with the simulation?

A. The feedback resistor is open  
B. The input capacitor is too large  
C. The supply voltage is too high  
D. The load resistance is increased

Answer:

```text
A
```

This is harder and more interesting, but you should add it after the basic pipeline works.

#### H. Cross-modal questions

If you want MMMU-like multimodal examples, include:

- schematic image
- netlist
- waveform plot
- Bode plot
- table of values

Then ask questions that require visual interpretation.

Example:

> From the plotted transient response, what is the approximate peak output voltage?

Or:

> According to the schematic and AC plot, is this circuit acting as a low-pass or high-pass filter?

This makes your dataset much closer to MMMU.

---

## 4. Recommended data item format

Each generated example could look like this:

```json
{
  "id": "rc_lowpass_000001",
  "family": "filter",
  "topology": "rc_lowpass",
  "difficulty": 1,
  "netlist": "* RC low-pass filter\nVin in 0 AC 1\nR1 in out 18.2k\nC1 out 0 4.7n\n.ac dec 50 1 10Meg\n.print ac V(out)\n.end",
  "parameters": {
    "R1_ohm": 18200,
    "C1_f": 4.7e-9
  },
  "simulation": {
    "type": "ac",
    "tool": "Xyce",
    "status": "success"
  },
  "features": {
    "cutoff_frequency_hz": 1860.3,
    "gain_db_at_100hz": -0.02,
    "gain_db_at_1khz": -1.1,
    "gain_db_at_10khz": -14.8,
    "behavior": "low_pass"
  },
  "artifacts": {
    "schematic_image": "images/rc_lowpass_000001.png",
    "bode_plot": "plots/rc_lowpass_000001_bode.png"
  },
  "qa": [
    {
      "question_type": "derived_numeric",
      "question": "What is the approximate -3 dB cutoff frequency of this circuit?",
      "answer": "1.86 kHz",
      "answer_value": 1860.3,
      "unit": "Hz"
    },
    {
      "question_type": "classification",
      "question": "Based on the AC response, what type of filter is this circuit?",
      "choices": ["Low-pass", "High-pass", "Band-pass", "Band-stop"],
      "answer": "Low-pass"
    }
  ]
}
```

---

## 5. Practical architecture

Structure the code like this:

```text
dataset_generator/
  templates/
    rc_lowpass.py
    rc_highpass.py
    voltage_divider.py
    diode_rectifier.py
    opamp_inverting.py

  netlist/
    writer.py

  simulation/
    xyce_runner.py
    parsers.py

  extraction/
    ac_features.py
    tran_features.py
    dc_features.py

  questions/
    templates.py
    numeric_questions.py
    classification_questions.py
    comparison_questions.py

  rendering/
    schematic_renderer.py
    plot_renderer.py

  validation/
    filters.py
    answer_checker.py

  generate_dataset.py
```

The core flow:

```python
for template in templates:
    circuit = template.sample()
    netlist = write_netlist(circuit)
    result = run_xyce(netlist)

    if not result.success:
        continue

    features = extract_features(result)

    if not passes_quality_filters(circuit, features):
        continue

    qa_pairs = generate_questions(circuit, features)

    save_example(circuit, netlist, result, features, qa_pairs)
```

---

## 6. Important quality filters

You need automatic rejection rules.

Reject circuits if:

- Xyce simulation fails
- output is all NaN or constant
- operating point is unrealistic
- node voltage is absurdly large
- current is absurdly large
- waveform does not settle when expected
- cutoff frequency is outside simulated range
- multiple-choice distractors are ambiguous
- the answer depends on arbitrary numerical tolerance
- generated plot does not visibly show the feature being asked about

For example, if asking about cutoff frequency, ensure:

```text
f_cutoff is inside the AC sweep range
gain actually drops by at least 3 dB
response is monotonic near cutoff
```

---

## 7. How to avoid data leakage

This is very important for benchmark quality.

Do not randomly split individual samples if many are just parameter variations of the same template.

Better splits:

### Easier split

Train/test split by parameter ranges.

Example:

```text
train: R from 1 kΩ to 100 kΩ
test: R from 100 kΩ to 1 MΩ
```

### Stronger split

Split by topology variants.

Example:

```text
train: RC low-pass, RC high-pass
test: loaded RC low-pass, RLC band-pass
```

### Strongest split

Hold out entire circuit families.

Example:

```text
train: passive filters and dividers
test: diode rectifiers or op-amp circuits
```

For MMMU-like evaluation, you probably want several splits:

```text
in-distribution
parameter extrapolation
topology generalization
family generalization
```

---

## 8. Use LLMs carefully

You can use an LLM for:

- paraphrasing questions
- generating natural explanations
- creating distractor wording
- making problem statements more human-like
- generating metadata tags

Do not use an LLM as the source of numerical truth.

Bad:

```text
Ask LLM: "What is the cutoff frequency?"
```

Good:

```text
Compute cutoff frequency from simulation.
Ask LLM: "Rewrite this question in a natural way without changing the answer."
```

For example, your deterministic template says:

```text
What is the -3 dB cutoff frequency of the circuit?
Answer: 1.86 kHz
```

The LLM can rewrite it as:

```text
From the Bode plot, estimate the frequency where the output first falls 3 dB below its low-frequency gain.
```

But your stored answer remains the computed one.

---

## 9. Concrete starting plan

If I were building this, I would start with the following MVP.

### MVP circuit families

Use only five templates:

1. Voltage divider
2. RC low-pass filter
3. RC high-pass filter
4. RLC band-pass filter
5. Half-wave rectifier

### MVP simulations

Use:

```text
.op
.dc
.ac
.tran
```

### MVP question types

Generate only:

1. Direct numeric questions
2. Derived numeric questions
3. Classification questions
4. Comparison questions

Example questions:

```text
What is the DC output voltage?
What is the approximate cutoff frequency?
Is the circuit low-pass or high-pass?
Which circuit has the larger output amplitude at 10 kHz?
What is the peak-to-peak ripple voltage?
```

This MVP is enough to validate your pipeline.

---

## 10. Example end-to-end item

Suppose your generator creates:

```spice
* RC low-pass
Vin in 0 AC 1
R1 in out 10k
C1 out 0 10n
.ac dec 100 1 10Meg
.print ac V(out)
.end
```

The theoretical cutoff is approximately:

```text
fc = 1 / (2πRC)
   = 1 / (2π × 10000 × 10e-9)
   ≈ 1591.5 Hz
```

Xyce simulation confirms approximately:

```json
{
  "low_freq_gain_db": 0.0,
  "cutoff_frequency_hz": 1592.0,
  "gain_db_at_10khz": -16.1,
  "behavior": "low_pass"
}
```

Then generate Q/A:

```json
[
  {
    "question": "What is the approximate -3 dB cutoff frequency of this circuit?",
    "answer": "1.59 kHz"
  },
  {
    "question": "At 10 kHz, is the output magnitude close to the input magnitude or significantly attenuated?",
    "answer": "It is significantly attenuated."
  },
  {
    "question": "What type of frequency response does this circuit exhibit?",
    "choices": ["Low-pass", "High-pass", "Band-pass", "Band-stop"],
    "answer": "Low-pass"
  }
]
```

---

## 11. Strongest suggestions

1. Use **template-based generation**, not arbitrary random circuits.
2. Store a **structured circuit record**, not only the netlist.
3. Run Xyce and extract a **fact table** from results.
4. Generate questions from the fact table using deterministic templates.
5. Use LLMs only for paraphrasing, not for ground truth.
6. Include schematic images and plots if you want MMMU-style multimodal data.
7. Split your benchmark by topology/family, not just random samples.
8. Start with a small MVP before scaling.

A good first milestone would be:

> Generate 1,000 examples from 5 circuit families, each with one schematic image, one simulation plot, and 3–5 verified Q/A pairs.

That will reveal most of the design problems before you invest in large-scale generation.
