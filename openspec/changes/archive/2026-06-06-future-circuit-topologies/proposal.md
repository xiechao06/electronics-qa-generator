## Why

The pipeline currently supports only 5 active circuit templates (voltage
divider, RC low-pass, RC high-pass, RLC band-pass, half-wave rectifier).
38 additional question templates for 9 more topologies are already written
in `questions/future_templates.py` but can't generate real Q/A items
without corresponding `CircuitTemplate` factories and `FACT_EXTRACTOR`
functions. Adding these 9 topologies triples the benchmark's circuit
diversity and covers ~130 additional MMMU-grounded question patterns
(transient analysis, phasor/impedance, transistor biasing, op-amp
configurations, resonance, network theorems).

## What Changes

- **New `CircuitTemplate` implementations** (9): `rc_step_response`,
  `rl_step_response`, `ac_phasor_rc`, `bjt_ce_amplifier`,
  `bjt_emitter_follower`, `mosfet_cs_amplifier`, `resistor_network`,
  `op_amp_inverting`, `rlc_series_resonance` — each in its own file
  under `templates/` with sampling logic, SPICE netlist emission,
  and `.tran` / `.ac` / `.op` simulation configs
- **New `FACT_EXTRACTOR` functions** (9): parse Xyce output into
  canonical fact dicts, registered in `extraction/facts.py`
- **Move question templates**: 38 templates from
  `questions/future_templates.py` → `questions/templates.py`
  (activate them in `QUESTION_TEMPLATES` registry)
- **New SVG schematic templates** (9): hand-authored SVG layouts
  with `slot-<REF>` / `slot-node-<NODE>` placeholders, registered
  in `render/svg_templates.py`, **all wire connections fully joined**
  (no disconnected components)
- **Update `ALL_TEMPLATES`** in `templates/__init__.py` to include
  the 9 new template classes

## Capabilities

### New Capabilities

- `rc-step-response`: RC circuit transient analysis — time constant τ,
  capacitor initial/final/τ voltage, comparison to 1 ms
- `rl-step-response`: RL circuit transient analysis — time constant τ = L/R,
  inductor initial/final/τ current, power at τ
- `ac-phasor-rc`: Single-frequency AC phasor analysis — capacitor voltage
  magnitude/phase, impedance magnitude/phase, average power
- `bjt-ce-amplifier`: BJT common-emitter DC bias + small-signal gain —
  V_CE_Q, I_C_Q, A_v, operating region classification
- `bjt-emitter-follower`: BJT common-collector analysis — output resistance
  r_out, voltage gain A_v (near unity)
- `mosfet-cs-amplifier`: MOSFET common-source analysis — V_DS_Q, I_D_Q,
  unbypassed voltage gain A_v
- `resistor-network`: Multi-resistor DC network with Thevenin equivalents —
  R_eq, V_th, R_th, source power
- `op-amp-inverting`: Ideal op-amp inverting amplifier — closed-loop gain,
  DC output voltage, −3 dB bandwidth
- `rlc-series-resonance`: Series RLC resonance — resonant frequency f_r,
  quality factor Q, bandwidth, impedance at resonance

### Modified Capabilities

<!-- None — pure additions, no existing spec changes -->

## Impact

- `src/electronics_qa_generator/templates/` — 9 new module files + update `__init__.py`
- `src/electronics_qa_generator/extraction/facts.py` — 9 new extractor functions + registry entries
- `src/electronics_qa_generator/questions/templates.py` — add 9 entries to `QUESTION_TEMPLATES`
- `src/electronics_qa_generator/questions/future_templates.py` — remove moved entries (or keep as reference)
- `src/electronics_qa_generator/render/svg/` — 9 new SVG layout files
- `src/electronics_qa_generator/render/svg_templates.py` — 9 registry entries
- `tests/` — new test modules for each template (sampling, netlist, extraction)
