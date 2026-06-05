# CLEVR-Style Algorithm for an Electronics Circuit Generator

This document proposes a **CLEVR-style circuit generation algorithm** for building a simulator-grounded electronics QA dataset.

The guiding idea is the same as CLEVR:

> **Randomly generate structured worlds, reject invalid or ambiguous cases, and keep exact symbolic ground truth for question generation.**

In CLEVR, the world is a 3D scene. Here, the world is a **circuit + simulation setup + measured behavior**.

---

## 1. Design goals

The circuit generator should produce examples that are:

- **valid**: simulation runs successfully
- **diverse**: many topologies and parameter regimes
- **nontrivial**: not all answers are obvious or constant
- **unambiguous**: measured quantities are clearly defined
- **grounded**: every answer can be traced to simulation outputs
- **reproducible**: every sample can be regenerated from metadata

---

## 2. CLEVR-to-circuits mapping

| CLEVR | Circuit generator |
|---|---|
| scene grammar | circuit family/template library |
| object attributes | component values, source settings, loads, temperature |
| object placement | component instantiation + parameter assignment |
| geometric constraints | circuit validity constraints |
| scene graph | netlist + circuit graph + metadata |
| rendered image | schematic + plots |
| functional program | executable question program |
| answer from scene | answer from simulator facts |

---

## 3. High-level algorithm

```text
1. Choose a circuit family and topology template.
2. Sample legal component values and operating conditions.
3. Build a candidate circuit instance.
4. Run symbolic/static validity checks.
5. Emit a SPICE/Xyce netlist.
6. Run required simulations.
7. Reject failed, unstable, trivial, or ambiguous cases.
8. Extract canonical facts from simulation outputs.
9. Render optional artifacts: schematic, waveform, Bode plot.
10. Save full structured metadata for later QA generation.
```

This is fundamentally:

> **template sampling + constrained randomization + simulation-backed rejection sampling**

---

## 4. Core data structures

Each accepted sample should store at least:

```json
{
  "id": "rc_lowpass_000123",
  "family": "filter",
  "topology": "rc_lowpass",
  "parameters": {
    "R1_ohm": 10000,
    "C1_f": 1e-8
  },
  "stimulus": {
    "source_type": "ac",
    "amplitude_v": 1.0
  },
  "simulation": {
    "analyses": ["ac"],
    "sweep": {"start_hz": 1, "stop_hz": 1e7, "ppd": 100}
  },
  "netlist": "...",
  "facts": {
    "cutoff_frequency_hz": 1591.5,
    "gain_db_at_10khz": -16.1,
    "behavior": "low_pass"
  },
  "artifacts": {
    "schematic": "...",
    "plot": "..."
  }
}
```

---

## 5. Circuit grammar

The generator starts from a **library of circuit templates**.

Each template defines:

- topology graph
- component slots
- legal parameter distributions
- valid simulation types
- measurable outputs
- rejection rules
- optional variants

Example template families:

- voltage divider
- RC low-pass
- RC high-pass
- RLC band-pass
- half-wave rectifier
- full-wave rectifier
- op-amp inverting amplifier
- BJT common-emitter amplifier
- MOSFET common-source amplifier

A template record might look like:

```python
Template(
    family="filter",
    name="rc_lowpass",
    nodes=["in", "out", "0"],
    components=[
        Resistor("R1", "in", "out"),
        Capacitor("C1", "out", "0")
    ],
    parameter_space={
        "R1": LogUniform(1e3, 1e6),
        "C1": LogUniform(1e-11, 1e-6)
    },
    analyses=["ac"],
    measurements=["cutoff_frequency", "gain_db", "phase_deg"],
    constraints=["grounded", "no_floating_nodes", "cutoff_in_range"]
)
```

This is the circuit equivalent of CLEVR’s object vocabulary and scene grammar.

---

## 6. Sampling algorithm

### Step 1: choose a template

Sample a family and a topology template, optionally under balancing constraints.

```python
family = sample_family(balance_state)
template = sample_template(family)
```

### Step 2: sample parameters

Sample component values from constrained distributions.

Examples:
- resistor: log-uniform over decades
- capacitor: log-uniform
- supply voltage: discrete set
- load resistance: bounded range
- frequency sweep bounds: selected to cover expected behavior

```python
params = {
    slot: template.parameter_space[slot].sample(rng)
    for slot in template.parameter_space
}
```

### Step 3: sample operating conditions

Sample:
- source type
- source amplitude
- DC offset
- load
- temperature
- optional parasitics
- optional variants or perturbations

```python
stimulus = sample_stimulus(template)
load = sample_load(template)
temperature = sample_temperature(template)
variant = sample_optional_variant(template)
```

### Step 4: instantiate candidate circuit

Create a concrete circuit object.

```python
candidate = instantiate(template, params, stimulus, load, temperature, variant)
```

---

## 7. Pre-simulation validity checks

Before running Xyce, reject obviously bad circuits.

### Static checks

- all required nodes connected
- at least one ground reference exists
- no floating subgraphs
- no illegal short of supply to ground
- no missing model for active device
- no malformed topology

### Topology checks

- component count within expected range
- probe nodes exist
- expected output node exists
- optional subcircuits are consistently wired

### Heuristic sanity checks

- no absurd component values
- expected RC or RLC scales are reasonable
- sweep range likely contains the target phenomenon

Example:

```python
if not is_grounded(candidate): reject
if has_floating_nodes(candidate): reject
if violates_template_constraints(candidate): reject
if not expected_measurements_are_defined(candidate): reject
```

This is analogous to CLEVR rejecting illegal object placements before rendering.

---

## 8. Netlist generation

Convert the candidate circuit into a deterministic Xyce/SPICE netlist.

Include:
- title/comments
- component declarations
- source definitions
- model definitions if needed
- analysis directives (`.op`, `.dc`, `.ac`, `.tran`)
- print/save directives

```python
netlist = write_netlist(candidate)
```

Store the netlist as part of the latent truth.

---

## 9. Simulation stage

Run one or more analyses depending on the template.

Typical choices:

- `.op` for DC operating point
- `.dc` for DC sweep questions
- `.ac` for frequency-response questions
- `.tran` for waveform/ripple/transient questions

```python
result = run_xyce(netlist)
if not result.success:
    reject
```

This is where circuits differ from CLEVR: instead of rendering only, we also compute **behavioral truth** through physics simulation.

---

## 10. Post-simulation rejection rules

This is the most important stage. Many circuit instances should be discarded.

### A. Numerical failure rejection

Reject if:
- solver does not converge
- outputs are NaN/Inf
- files are incomplete
- expected traces are missing

### B. Physical absurdity rejection

Reject if:
- voltages or currents are clearly unrealistic for the intended family
- operating point is pathological
- active device is entirely off when that defeats the intended task

### C. Triviality rejection

Reject if the question target is too obvious or uninformative.

Examples:
- gain curve is essentially flat when you wanted a filter
- ripple is almost zero when asking about ripple magnitude
- two compared variants produce nearly identical values
- output clipped/not-clipped classification is numerically marginal

### D. Ambiguity rejection

Reject if:
- cutoff is outside sweep range
- multiple possible resonant peaks make the question ambiguous
- waveform does not settle enough to define steady state
- plot feature is too visually subtle for a visual QA version

### E. Coverage-balancing rejection

Reject or downsample if:
- too many samples from one family
- too many low-pass labels
- too many open questions vs multiple choice

This is the circuit analogue of CLEVR’s degeneracy and ambiguity checks.

---

## 11. Fact extraction algorithm

After successful simulation, compute a **canonical fact table**.

Examples by analysis type:

### `.op`
- node voltages
- branch currents
- device region label if inferable

### `.dc`
- output at specific input values
- monotonic increase/decrease
- threshold crossings

### `.ac`
- low-frequency gain
- high-frequency gain
- -3 dB cutoff frequency
- resonant frequency
- peak gain
- phase at target frequency
- response class: low-pass / high-pass / band-pass / band-stop

### `.tran`
- peak value
- min value
- steady-state value
- rise time
- settling time
- overshoot
- ripple peak-to-peak
- clipping indicator

Example:

```python
facts = extract_facts(result, candidate)
```

Representative output:

```json
{
  "low_freq_gain_db": -0.01,
  "cutoff_frequency_hz": 1591.5,
  "gain_db_at_1khz": -1.45,
  "gain_db_at_10khz": -16.1,
  "phase_deg_at_10khz": -81.2,
  "behavior": "low_pass"
}
```

This fact table is the circuit equivalent of CLEVR’s scene graph plus relation table.

---

## 12. Informativeness scoring

A useful addition beyond CLEVR is to score how useful a circuit is for QA.

Example score components:

- simulation success: required
- target feature visibility: high if clear
- nontriviality: high if values are not degenerate
- question diversity contribution: high if this sample adds rare coverage
- visual clarity: high if plots are clean

```python
def informativeness_score(candidate, facts):
    score = 0
    score += clear_feature_score(facts)
    score += diversity_bonus(candidate)
    score += visual_support_score(candidate, facts)
    score -= ambiguity_penalty(facts)
    return score
```

Accept only if score exceeds a threshold.

---

## 13. Optional variant generation

To support comparison and counterfactual questions, create related variants.

Examples:
- double `C1`
- halve `Rload`
- change supply voltage
- swap one component value decade
- add/remove load

Algorithm:

```python
variant = perturb(candidate, rule="double_C1")
variant_result = run_xyce(write_netlist(variant))
variant_facts = extract_facts(variant_result, variant)
```

Then store relation facts:

```json
{
  "original_cutoff_hz": 1591.5,
  "variant_cutoff_hz": 795.7,
  "cutoff_relation": "decreases"
}
```

This is the circuit equivalent of CLEVR’s compositional reasoning extension.

---

## 14. Rendering artifacts

For multimodal QA, render:

- schematic image
- Bode plot
- transient waveform
- DC sweep plot
- optional table or annotation image

Rendering must also be validated.

Reject if:
- axes are unreadable
- traces overlap confusingly
- key feature is off-scale
- image resolution is too low

This is analogous to CLEVR rendering the final scene image.

---

## 15. Save structured latent truth

For every accepted sample, save:

- template ID
- family
- parameter values
- operating conditions
- netlist
- simulation config
- raw result file paths
- extracted facts
- optional variant facts
- rendered artifact paths
- random seed

This guarantees reproducibility and answer traceability.

---

## 16. Pseudocode

```python
def generate_circuit_sample(rng):
    while True:
        template = sample_template(rng)
        params = sample_parameters(template, rng)
        stimulus = sample_stimulus(template, rng)
        load = sample_load(template, rng)
        temperature = sample_temperature(template, rng)
        variant_flags = sample_optional_variants(template, rng)

        candidate = instantiate(
            template=template,
            params=params,
            stimulus=stimulus,
            load=load,
            temperature=temperature,
            variant_flags=variant_flags,
        )

        if not static_valid(candidate):
            continue

        netlist = write_netlist(candidate)
        result = run_xyce(netlist)
        if not result.success:
            continue

        facts = extract_facts(result, candidate)

        if not passes_postsim_checks(candidate, facts, result):
            continue

        score = informativeness_score(candidate, facts)
        if score < MIN_SCORE:
            continue

        artifacts = render_artifacts(candidate, result, facts)
        if not artifacts_are_clear(artifacts, facts):
            continue

        sample = {
            "template": template.name,
            "family": template.family,
            "params": params,
            "stimulus": stimulus,
            "load": load,
            "temperature": temperature,
            "netlist": netlist,
            "facts": facts,
            "artifacts": artifacts,
            "seed": current_seed(),
        }

        return sample
```

---

## 17. Question-generation readiness

The generator is successful if every accepted sample supports one or more executable question programs, such as:

- `query_dc_voltage(node="out")`
- `measure_gain_db(freq=1000)`
- `find_cutoff_db(drop=3)`
- `classify_response_type()`
- `compare_variant(metric="cutoff_frequency")`
- `measure_ripple_pp(node="out")`

This is the direct analogue of CLEVR functional programs.

---

## 18. Recommended generation stages

### Stage 1: Canonical templates
Generate only simple textbook circuits.

Purpose:
- validate the pipeline
- establish clean fact extraction
- produce stable first QA items

### Stage 2: Parameter variation
Broaden ranges of values and operating conditions.

Purpose:
- improve diversity
- avoid overfitting to fixed scales

### Stage 3: Perturbed realism
Add loads, source resistance, ESR, nonideal models.

Purpose:
- make examples more realistic
- support richer questions

### Stage 4: Compositional circuits
Combine multiple blocks.

Purpose:
- support multi-step reasoning
- create harder multimodal examples

---

## 19. Why this is CLEVR-like

This algorithm follows the same spirit as CLEVR because it:

- starts from a **controlled world grammar**
- uses **random sampling under constraints**
- applies **rejection sampling** to remove bad cases
- saves **exact latent structure**
- enables **executable question programs**
- supports **fine-grained evaluation by reasoning skill**

The main difference is that the world truth is not only geometric; it is also **physical**, obtained through simulation.

---

## 20. Bottom line

A CLEVR-style electronics circuit generator should be built as:

> **template-driven circuit sampling + static validity checks + simulator-backed rejection sampling + structured fact extraction**

In one line, the algorithm is:

> **Sample a circuit template, instantiate it with constrained parameters, reject invalid or uninformative simulations, and save the surviving circuit together with its exact simulation-backed fact table.**

That gives a solid foundation for deterministic, high-quality, simulator-grounded QA generation.
