## Context

The pipeline architecture (docs/architecture.md) defines a clear pattern for
activating a circuit topology: `CircuitTemplate` → netlist → Xyce simulation →
`FACT_EXTRACTOR` → `QUESTION_TEMPLATES` → schematics. Five topologies already
follow this pattern (passive.py, rectifier.py). Nine more have question
templates ready (future_templates.py) but lack the upstream stages.

The SVG schematic renderer already supports hand-authored templates with
`slot-<REF>` placeholders — the 5 existing SVGs are in `render/svg/` and
registered in `render/svg_templates.py`. The same pattern applies to the 9
new topologies.

## Goals / Non-Goals

**Goals:**
- Implement all 9 backlog topologies end-to-end (sample → simulate → extract → question)
- Every SVG template must have fully-connected wires (endpoints shared between segments, no gaps to symbol boundaries)
- Follow existing patterns exactly (CircuitGraph, CircuitRecord, SimulationConfig)
- Question templates move from `future_templates.py` to `templates.py` unchanged

**Non-Goals:**
- Adding new question templates beyond the 38 already written
- Changing the Xyce simulation runner or parser
- Adding simulation types not already supported (.op, .ac, .tran)
- Modifying the validation pipeline (all checks work as-is on new topologies)
- Adding new circuit families not in the backlog

## Decisions

### 1. One template file per topology group

**Decision**: Group related templates by circuit family: `transient.py`
(rc_step_response, rl_step_response), `bjt.py` (bjt_ce_amplifier,
bjt_emitter_follower), `mosfet.py` (mosfet_cs_amplifier),
`op_amp.py` (op_amp_inverting), `network.py` (resistor_network,
ac_phasor_rc, rlc_series_resonance).

**Rationale**: The 5 existing topologies are split into `passive.py` and
`rectifier.py` (family grouping). Grouped files share constants (E-series
values, SPICE models), reduce boilerplate, and make it easier to add more
topologies within a family later.

**Alternative**: One file per topology (9 files). Rejected because it scatters
shared definitions (e.g., BJT model params between CE and EF) and makes
future additions harder to discover.

### 2. SVG layout topology

All 9 SVGs use the same rail-and-drop pattern proven in the existing 5 SVGs:
- Voltage source on the left (vertical, circle symbol with +/−)
- Series components on the top rail (horizontal, left to right)
- Last component drops vertically to the bottom rail
- Ground symbol at source bottom
- Node labels (`in`, `out`, `mid`) as `slot-node-*` text elements

**Connection rules** (verified by the SVG disconnection fixes):
- Wire segments share exact endpoint coordinates at junctions
- Leads touch symbol boundaries (plate edge for capacitors, circle boundary for sources)
- No 2px "near-miss" gaps — leads end exactly at x or y of the symbol edge

### 3. Transient simulation timing

For `.tran` templates (rc_step_response, rl_step_response):
- Step input modeled as a PWL (piecewise-linear) source: 0 V before t=1 μs, V_step after
- Simulate for 10τ to capture steady state
- Extract initial/final/τ values from the waveform directly

**Rationale**: Xyce PWL sources provide clean step edges without ideal-switch
complexity. The 1 μs delay ensures consistent initial conditions before the
step.

### 4. Op-amp model

For `op_amp_inverting`, use Xyce's built-in voltage-controlled voltage source
(E element) with gain = 1e5 as the ideal op-amp model, plus R_in = 1 MΩ and
R_out = 75 Ω for realistic behavior. No external SPICE model file needed.

### 5. BJT model

For `bjt_ce_amplifier` and `bjt_emitter_follower`, use a 2N2222 NPN model
with standard SPICE parameters. Include β variation: sample β from {100, 150,
200, 300} and scale IS accordingly. Model directive included via
`graph.add_directive()`.

## Risks / Trade-offs

- **BJT simulation non-convergence** → Xyce may fail on some bias combinations
  (e.g., R1/R2 ratios that put the transistor in cutoff). Mitigation: use
  `template.sample()` with retry logic (draw 3 samples, use first that
  converges).
- **Transient timing precision** → PWL step at t=1 μs and measurement at
  t=1τ may have small numerical error. Mitigation: set `time_step` fine enough
  (τ/1000) and use cubic interpolation for fact extraction.
- **Op-amp bandwidth** → Ideal E-element has infinite bandwidth. For −3 dB
  measurement, add a dominant pole via RC at the output to get a measurable
  roll-off.
- **MOSFET model parameters** → Default NMOS Level=1 model in Xyce with
  VTO, KP, LAMBDA. Sampled within physically plausible ranges for a
  small-signal NMOS (e.g., 2N7002-like).
