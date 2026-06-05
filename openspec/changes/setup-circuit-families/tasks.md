## 1. Template framework foundation

- [x] 1.1 Create `templates/base.py`: `CircuitTemplate` ABC with `family`, `topology` class attributes and abstract `sample(self, seed: int | None = None) -> CircuitRecord` method
- [x] 1.2 Create `templates/parameter.py`: `Uniform`, `LogUniform`, `Choice` distribution classes, each with `sample(rng: random.Random) -> float`
- [x] 1.3 Create `templates/e_series.py`: `E6_CAPACITOR_VALUES` and `E12_RESISTOR_VALUES` constants plus a `pick_e_value(values, decades, rng)` helper
- [x] 1.4 Create `templates/netlist_helpers.py`: `format_netlist(template, params) -> str` with value formatting (k/Meg suffixes for resistors, n/u/p for capacitors)

## 2. Passive circuit templates

- [x] 2.1 Implement `templates/passive.py::VoltageDivider`: E12 R1/R2 (100Ω–1MΩ), DC Vin (1–30V), `.op` netlist, probed at V(out), difficulty=1
- [x] 2.2 Implement `templates/passive.py::RCLowPass`: E12 R (1kΩ–1MΩ), E6 C (100pF–10μF), `.ac` sweep 1Hz–10MHz @ 50 pts/dec, probed at V(out), difficulty=1
- [x] 2.3 Implement `templates/passive.py::RCHighPass`: same parameter ranges as low-pass but high-pass topology (C in series, R to ground)
- [x] 2.4 Implement `templates/passive.py::RLCBandPass`: E12 R (100Ω–10kΩ), inductor (1mH–100mH selected values), E6 C (10nF–1μF), series RLC with output across R, `.ac` 10Hz–10MHz

## 3. Diode circuit templates

- [x] 3.1 Implement `templates/rectifier.py::HalfWaveRectifier`: E12 R_load (1kΩ–100kΩ), E6 C_filter (1μF–100μF), AC source 1–20V @ 60Hz, `.tran` ≥10 periods, 1N4148 diode, difficulty=1

## 4. Integration and exports

- [x] 4.1 Create `ALL_TEMPLATES` list in `templates/__init__.py` containing one instance of each concrete template class
- [x] 4.2 Update `templates/__init__.py` to export all public symbols (`CircuitTemplate`, distributions, E-series helpers, format_netlist, each template class, `ALL_TEMPLATES`)

## 5. Tests

- [x] 5.1 Write `tests/test_templates/test_framework.py`: test `CircuitTemplate` ABC enforcement, distribution bounds and determinism, E-series value lists, `format_netlist` output
- [x] 5.2 Write `tests/test_templates/test_passive.py`: test each passive template's `sample()` output — correct family/topology, parameter keys, netlist syntax (`.ac`/`.op`, component placement), simulation type, probe list
- [x] 5.3 Write `tests/test_templates/test_rectifier.py`: test `HalfWaveRectifier.sample()` — family/topology, parameter keys, netlist contains `D1` and diode model, `.tran` with adequate stop time
- [x] 5.4 Write `tests/test_templates/test_registry.py`: test `ALL_TEMPLATES` has exactly 5 items with distinct topologies
- [x] 5.5 Write `tests/test_templates/test_reproducibility.py`: test that same seed → identical `CircuitRecord`, different seeds → different output
- [x] 5.6 Write `tests/test_templates/test_ac_coverage.py`: test that RC low-pass and high-pass templates' theoretical cutoff falls within sweep range

## 6. Verification

- [x] 6.1 Run `uv run pytest tests/test_templates/ -v` — all tests pass
- [x] 6.2 Run `uv run ruff check .` — no lint errors
- [x] 6.3 Run `uv run ruff format --check .` — code is properly formatted
- [x] 6.4 Run `uv run eqa generate -n 5` — CLI still loads without errors (pipeline still NotImplemented, but imports work)
