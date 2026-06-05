## Why

The pipeline's first stage — the template library — is a stub with no real circuit families. Without concrete circuit templates, the sampler, netlist generator, and every downstream stage have nothing to generate from. Getting five MVP circuit families wired up unblocks the entire pipeline and lets us validate the full data flow end-to-end before scaling.

## What Changes

- Define a **base template class** (`CircuitTemplate`) with a `sample()` contract that returns a structured `CircuitRecord` (parameterized values, topology metadata, simulation config, probes, and rejection rules).
- Implement a **parameter distribution system** (log-uniform, uniform, choice) for constrained randomization of component values, supply voltages, and stimulus parameters.
- Add **netlist emission helpers** — functions that turn a sampled circuit record into valid Xyce/SPICE netlists for `.op`, `.dc`, `.ac`, and `.tran` analyses.
- Create **five MVP circuit templates** that each generate valid, simulator-ready netlists with independent parameter randomization:

| Family | Circuit | Simulation type | Key facts extracted |
|---|---|---|---|
| Passive | Voltage divider | `.op` | Node voltages, divider ratio |
| Passive | RC low-pass filter | `.ac` | Cutoff frequency, gain vs frequency |
| Passive | RC high-pass filter | `.ac` | Cutoff frequency, gain vs frequency |
| Passive | RLC band-pass filter | `.ac` | Center frequency, bandwidth |
| Diode | Half-wave rectifier | `.tran` | Peak output, ripple, steady-state voltage |

- **Test every template** with deterministic (seeded) sampling: verify that `sample()` produces consistent parameter values, valid netlist syntax, and populated `CircuitRecord` fields.

## Capabilities

### New Capabilities
- `template-framework`: Base `CircuitTemplate` class with abstract `sample()`, parameter distribution system (uniform, log-uniform, choice), and netlist emission helpers for binding sampled parameters into valid Xyce/SPICE netlists. Integrates with `models.CircuitRecord`.
- `circuit-templates`: Five concrete templates — voltage divider, RC low-pass, RC high-pass, RLC band-pass, half-wave rectifier — each implementing `CircuitTemplate` with topology-specific parameter ranges, simulation configs, probe lists, and netlist templates for `.op`, `.ac`, or `.tran`.

### Modified Capabilities
<!-- None — this is the first real capability being built. -->

## Impact

- **Package:** `src/electronics_qa_generator/templates/` (new `base.py`, `parameter.py`, `netlist_helpers.py`, plus one module per circuit family)
- **Models:** `models.py` may need minor extensions (e.g., confirm `netlist` field shape, add `seed` to `CircuitRecord`)
- **No dependencies beyond stdlib for the templates themselves** — `numpy` is available but not required yet (random module suffices for seeded sampling)
- **Tests:** new `tests/test_templates/` directory with deterministic output tests
