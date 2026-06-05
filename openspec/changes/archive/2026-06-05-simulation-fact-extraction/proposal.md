## Why

Five templates generate valid Xyce netlists, but we have no way to run them, extract facts, or know whether a circuit is interesting. The pipeline is missing the stage that makes it a BENCHMARK generator rather than a netlist generator: simulation-backed ground truth. Until we can run Xyce and extract measurable facts, no QA items can be produced. Simulation, fact extraction, and caching are one logical pipeline stage — extraction needs simulation output, and caching avoids re-running Xyce for the same circuit.

## What Changes

- A **Xyce runner** in `simulation/runner.py` that takes a netlist string, writes a temp `.cir` file, invokes Xyce, captures stdout/stderr, and returns a `SimResult` (success/failure, raw output, exit code). Configurable timeout per run; capture convergence errors gracefully.
- A **retry-with-perturbation** wrapper: if Xyce fails, perturb resistor values slightly on the `CircuitGraph` and retry (up to 3 attempts). This borrows directly from AutoCkt's failure handling.
- **Output parsers** in `extraction/parsers.py` — one function per simulation type (`parse_op`, `parse_ac`, `parse_tran`, `parse_dc`) that parse Xyce `.print` output into structured data (dicts/DataFrames of voltage/current vs. frequency/time).
- **Fact extractors** in `extraction/facts.py` — compute canonical facts from parsed data: DC output voltage (`V(out)` for `.op`), cutoff frequency and passband gain for `.ac`, ripple Vpp and DC level for `.tran`, behavior classification (low-pass, high-pass, band-pass).
- A **fact cache** (`simulation/cache.py`) keyed by `(topology, seed)` storing parsed facts dicts to disk (JSON or pickle). Before running Xyce, check cache; after running, write cache. Makes QA generation instant for pre-simulated circuits.
- A **sample richness score**: after fact extraction, compute whether the sample is "interesting" (facts are well-separated from other samples, simulation is numerically stable, probes produced non-degenerate output). Low-scoring samples can be filtered in the dataset assembler.
- Wire the runner into `eqa simulate` subcommand: given a topology and seed (or `--all`), run Xyce, extract facts, print or save.

## Capabilities

### New Capabilities
- `simulation-runner`: Xyce invocation with subprocess management, timeout, retry-with-perturbation, `SimResult` data class, and `run_xyce(graph, simulation_config, retries=3, timeout_s=30)`.
- `output-parsing`: Parse Xyce `.print op`/.ac/.tran/.dc output into structured numeric data. Handle multi-column output (multiple probes) and frequency/time sweeps.
- `fact-extraction`: Compute canonical facts from parsed simulation output: DC voltages, AC cutoff/gain/phase, transient ripple/DC-level, behavior classification. Each template defines which facts to extract.
- `fact-cache`: Disk-backed cache `{(topology, seed) → fact_dict}` with JSON serialization. Check-then-write pattern. Cache directory configurable.
- `sample-scoring`: Compute a richness/quality score for each sample based on fact separability, numerical stability, and probe coverage.

## Impact

- **New code:** `simulation/runner.py`, `simulation/cache.py`, `extraction/parsers.py`, `extraction/facts.py`, `simulation/models.py` (SimResult)
- **Modified:** `simulation/__init__.py`, `extraction/__init__.py` — exports
- **New capability:** `models.py` — may add `SimResult` or keep in `simulation/models.py`
- **CLI:** new `eqa simulate` subcommand alongside `emit`
- **Dependencies:** Xyce installed on PATH (no Python bindings needed — subprocess call). All Python code uses stdlib (`subprocess`, `json`, `pathlib`). Optional `numpy` for AC/tran array parsing (can fall back to pure Python).
- **Tests:** require Xyce on PATH for integration tests; unit tests mock the subprocess call
