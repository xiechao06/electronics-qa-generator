## 1. Simulation models

- [x] 1.1 Create `simulation/models.py` with `SimResult` dataclass (success, sim_type, raw_output, exit_code, error_message, converged)
- [x] 1.2 Export `SimResult` from `simulation/__init__.py`

## 2. Xyce runner

- [x] 2.1 Create `simulation/runner.py` with `invoke_xyce(netlist, timeout_s=30)` — writes temp `.cir`, runs `xyce`, captures output, detects convergence
- [x] 2.2 Add `check_xyce_installed()` — raises `RuntimeError` with helpful message if `xyce` not on PATH
- [x] 2.3 Implement `run_xyce_with_retry(graph, simulation, max_attempts=3, timeout_s=30)` — perturb resistor values by ±5% on failure, re-emit, retry
- [x] 2.4 Add perturbation helper: `_perturb_resistors(graph, rng, delta=0.05)` — multiply each resistor value by random factor in [0.95, 1.05]

## 3. Output parsers

- [x] 3.1 Create `extraction/parsers.py` with `parse_op(raw_output: str) -> dict[str, float]`
- [x] 3.2 Add `parse_ac(raw_output: str) -> dict[str, list[tuple[float, float]]]`
- [x] 3.3 Add `parse_tran(raw_output: str) -> dict[str, list[tuple[float, float]]]`
- [x] 3.4 Export parsers from `extraction/__init__.py`

## 4. Fact extraction

- [x] 4.1 Create `extraction/facts.py` with `FACT_EXTRACTORS` registry dict
- [x] 4.2 Implement `find_cutoff_frequency(freqs, gains_db) -> float` — find −3 dB point relative to passband reference
- [x] 4.3 Implement voltage divider extractor — `Vout_dc`, `divider_ratio`
- [x] 4.4 Implement RC low-pass extractor — `cutoff_hz`, `passband_gain_db`, `behavior`
- [x] 4.5 Implement RC high-pass extractor — `cutoff_hz`, `passband_gain_db`, `behavior`
- [x] 4.6 Implement RLC band-pass extractor — `center_freq_hz`, `bandwidth_hz`, `Q`, `peak_gain_db`
- [x] 4.7 Implement half-wave rectifier extractor — `Vout_peak`, `Vout_dc`, `ripple_vpp`
- [x] 4.8 Export `FACT_EXTRACTORS` and extractor functions from `extraction/__init__.py`

## 5. Fact cache

- [x] 5.1 Create `simulation/cache.py` with `FactCache` class (get, put, cache_dir)
- [x] 5.2 JSON serialization: `put` writes `<topology>_<seed:08x>.json`; `get` reads and deserializes
- [x] 5.3 Auto-create cache directory on first `put`
- [x] 5.4 Export `FactCache` from `simulation/__init__.py`

## 6. Richness scoring

- [x] 6.1 Create `extraction/scoring.py` with `RichnessScore` dataclass and `compute_richness(facts, sim_result, all_samples=None)`
- [x] 6.2 Neutral default: 0.5 for all fields, 1.0 probe_coverage on success, 0.0 on failure
- [x] 6.3 Export from `extraction/__init__.py`

## 7. CLI wiring

- [x] 7.1 Add `eqa simulate` subparser to `cli.py` with `--seed`, `--cache-dir`, `--no-cache`, `--all`
- [x] 7.2 Implement simulate handler: sample template → check cache → run Xyce → parse → extract facts → cache → print JSON

## 8. Tests

- [x] 8.1 Write `tests/test_simulation/test_runner.py` — mock subprocess for success/failure/timeout, retry logic, perturbation
- [x] 8.2 Write `tests/test_simulation/test_cache.py` — put/get, miss, directory auto-create, JSON round-trip
- [x] 8.3 Write `tests/test_extraction/test_parsers.py` — OP/AC/TRAN golden-file parsing, malformed input
- [x] 8.4 Write `tests/test_extraction/test_facts.py` — each extractor with known parsed data
- [x] 8.5 Write `tests/test_extraction/test_scoring.py` — rich score on success/failure

## 9. Verification

- [x] 9.1 Run `uv run pytest -v` — all tests pass
- [x] 9.2 Run `uv run ruff check .` and `uv run ruff format --check .` — clean
- [x] 9.3 Manual smoke: `uv run eqa simulate rc_lowpass --seed 42` (requires Xyce)
