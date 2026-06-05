## Why

Current templates build SPICE netlists as raw strings with `.format()` calls. This conflates circuit structure with serialization format, making it impossible to inspect topology, validate connectivity, or ask graph-based questions. All future stages — simulation validation, topology-aware QA generation, circuit perturbation — need to reason about nodes, components, and connections. A graph-centric representation separates structure from emission, aligning with CLEVR's scene-graph philosophy where the primary model is the graph and rendering is a downstream concern.

## What Changes

- Introduce two lightweight data structures: `CircuitGraph` (nodes + ordered components) and `Component` (kind, connectivity, params). These live alongside `CircuitRecord` in a new `graph/` subpackage.
- `CircuitGraph` provides methods to add components (`add_resistor`, `add_capacitor`, `add_vsource`, `add_diode`), query topology (node count, component count, connectivity), and validate (no floating nodes, no duplicate names).
- Add a `graph.to_spice(simulation: SimulationConfig)` method that produces a Xyce netlist string. This replaces manual string formatting in templates.
- Update `CircuitTemplate.sample()` to build a `CircuitGraph` instead of a raw `netlist` string. The `netlist` field on `CircuitRecord` is populated from `graph.to_spice()`, so **the public contract is backward-compatible** — downstream code (serializer, emit CLI, tests) sees the same `CircuitRecord.netlist` field.
- **Port all 5 existing templates** (voltage divider, RC low-pass, RC high-pass, RLC band-pass, half-wave rectifier) to the graph API. Template behavior (component ranges, simulation types, probes) is unchanged.
- Template string constants like `_VOLTAGE_DIVIDER_NETLIST` are removed — they are replaced by graph construction code.

## Capabilities

### New Capabilities
- `circuit-graph`: `CircuitGraph` and `Component` data structures, graph construction helpers (`add_resistor`, `add_capacitor`, `add_vsource`, `add_diode`), `to_spice()` emitter, and `validate()` for pre-simulation sanity checks.

### Modified Capabilities
<!-- None — template behavior and CircuitRecord output contract are unchanged. -->

## Impact

- **New package:** `src/electronics_qa_generator/graph/` with `models.py` (CircuitGraph, Component), `spice_emitter.py` (to_spice), `__init__.py`
- **Modified:** `templates/passive.py` — 4 template `sample()` methods rewritten to use graph API; netlist string constants removed
- **Modified:** `templates/rectifier.py` — 1 template `sample()` method rewritten
- **Models:** `models.py` — no changes; `CircuitRecord.netlist` still receives a string
- **Tests:** update existing template tests for graph-based construction; add new tests for `CircuitGraph` validation, `to_spice()` output, graph query methods
- **Dependencies:** stdlib only (`__future__.annotations`, `dataclasses`, `collections`)
- **Breaking:** none — `CircuitRecord` output is byte-identical to current behavior; `ALL_TEMPLATES` registry is unchanged; emit CLI produces identical files
