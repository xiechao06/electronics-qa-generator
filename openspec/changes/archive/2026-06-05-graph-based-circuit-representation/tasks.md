## 1. Graph data structures

- [x] 1.1 Create `graph/__init__.py` as a new subpackage with exports
- [x] 1.2 Create `graph/models.py` with `Component` and `CircuitGraph` dataclasses, including `add_resistor`, `add_capacitor`, `add_inductor`, `add_voltage_source` (dc/ac/sin), `add_diode` methods; also `node_count` and `component_count` properties, `nodes` (non-ground set property), `components_by_kind()`
- [x] 1.3 Write `graph/spice_emitter.py` with standalone `emit_spice(graph, simulation) -> str` that iterates components, emits one SPICE line per component using the value formatter, appends simulation card and `.print`, ends with `.end`
- [x] 1.4 Add `validate()` method to `CircuitGraph` returning `list[str]` — check unknown node refs, duplicate names, no sources, floating nodes, ground exists

## 2. Integrate graph into `CircuitTemplate`

- [x] 2.1 Add a convenience wrapper method `CircuitTemplate.build_graph() -> CircuitGraph` that returns a pre-initialized graph (or a helper in base.py)
- [x] 2.2 Expose `to_spice()` as a method on `CircuitGraph` that delegates to `emit_spice`

## 3. Port existing templates

- [x] 3.1 Port `VoltageDivider.sample()` — remove `_VOLTAGE_DIVIDER_NETLIST` constant, build graph, call `to_spice()`
- [x] 3.2 Port `RCLowPass.sample()` — remove `_RC_LOWPASS_NETLIST` constant, build graph, call `to_spice()`
- [x] 3.3 Port `RCHighPass.sample()` — remove `_RC_HIGHPASS_NETLIST` constant, build graph, call `to_spice()`
- [x] 3.4 Port `RLCBandPass.sample()` — remove `_RLC_BANDPASS_NETLIST` constant, build graph, call `to_spice()`
- [x] 3.5 Port `HalfWaveRectifier.sample()` — remove `_HALF_WAVE_NETLIST` constant (from rectifier.py), build graph, call `to_spice()`
- [x] 3.6 Remove unused netlist-string constants and any now-unnecessary imports (e.g., `_format_resistance` etc. from templates if only used via graph)

## 4. Update netlist helpers (if needed)

- [x] 4.1 Review `netlist_helpers.py` — if formatting helpers are now only called from `spice_emitter.py`, move them into `graph/` or keep as-is and import; ensure no duplication
- [x] 4.2 Re-export formatting helpers from appropriate location so templates don't need them

## 5. Tests — graph

- [x] 5.1 Write `tests/test_graph/test_models.py`: construction, node/component counts, `components_by_kind`, duplicate name detection
- [x] 5.2 Write `tests/test_graph/test_spice_emitter.py`: `to_spice()` for `.op`, `.ac`, `.tran`; value formatting (k, Meg, n, m); `.end` placement
- [x] 5.3 Write `tests/test_graph/test_validation.py`: floating node, missing ground, unknown node, duplicate name errors; valid circuit produces empty list

## 6. Tests — byte-identical template output

- [x] 6.1 Verify all existing template tests in `tests/test_templates/` still pass (they serve as golden-file regression tests)
- [x] 6.2 Add or update a reproducibility test confirming that same seed → same `CircuitRecord.netlist` string pre- and post-port

## 7. Verification

- [x] 7.1 Run `uv run pytest -v` — all tests pass (existing + new)
- [x] 7.2 Run `uv run ruff check .` and `uv run ruff format --check .` — clean
- [x] 7.3 Manual smoke: `uv run eqa emit rc_lowpass --seed 42` produces correct netlist output
- [x] 7.4 Confirm byte-identical output: capture current `VoltageDivider().sample(42).netlist`, then after port, confirm the same string is produced
