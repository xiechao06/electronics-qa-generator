## Context

Five templates emit Xyce netlists. The `simulation/` and `extraction/` subpackages exist as stubs. `CircuitGraph` provides structural validation; what's missing is the behavioral ground truth: running Xyce, parsing output, and extracting measurable facts. Python 3.14, stdlib + optional numpy. Xyce invoked as a subprocess (no Python bindings). We need the simulation stage to fail gracefully, not crash the pipeline.

## Goals / Non-Goals

**Goals:**
- Invoke Xyce from Python with a time budget (per-run timeout) and retry if it fails.
- Parse `.print op`, `.print ac`, `.print tran` output into structured data.
- Compute canonical facts from parsed data: DC voltages, cutoff frequency, gain, ripple, behavior classification.
- Disk-cache facts by `(topology, seed)` to avoid re-simulation.
- Score samples for richness (are the facts interesting?).
- Expose via `eqa simulate` CLI.

**Non-Goals:**
- Parallel/batch simulation (that's the orchestrator, a future change).
- Generating QA items from facts (that's the question engine).
- Schematic or waveform rendering (rendering stage).
- Installing Xyce (it's a system prerequisite, tested via `which xyce`).
- Supporting `.dc` sweep parsing right now (only OP, AC, TRAN for 5 templates).

## Decisions

### 1. SimResult as a lightweight dataclass

```python
@dataclass
class SimResult:
    success: bool
    sim_type: str  # "op", "ac", "tran"
    raw_output: str  # captured stdout
    exit_code: int
    error_message: str | None
    converged: bool  # True if Xyce reported convergence
```

Not a full parser — just the raw output. Fact extraction takes it from here.

### 2. Retry-with-perturbation

```python
def run_xyce_with_retry(netlist: str, max_attempts: int = 3, timeout_s: int = 30) -> SimResult:
```

On the first failure, re-generate the netlist with resistor values perturbed by ±5% (using the `CircuitGraph` to re-emit). This borrows from AutoCkt. If all attempts fail, return `SimResult(success=False)` with the error chain.

Rationale: SPICE convergence failures are often numerical luck — a slightly different R value can fix the operating point.

### 3. Parsing strategy: line-by-line state machines

Xyce `.print` output is formatted text, not a structured format. For each simulation type:

- `.op`: one line of values per probe. Parse: `Probe = Value` into a flat dict.
- `.ac`: header line with probe names, then data rows (frequency, magnitude, phase). Parse into lists of `(freq, mag_db)` tuples per probe.
- `.tran`: header line with probe names, then data rows (time, values). Parse into lists of `(time, value)` tuples per probe.

Example Xyce `.op` output:
```
Index   V(out)
------  ------
     0   3.14159
```

Example `.ac` output:
```
Index   FREQ            V(out)
------  --------        ------
     0   1.000000e-02    9.999987e-01
     1   1.258925e-02    9.999978e-01
```

Parsers are pure functions: `parse_op(raw: str) -> dict[str, float]`, `parse_ac(raw: str) -> dict[str, list[tuple[float, float]]]`.

### 4. Fact extraction: one function per template

Rather than a generic "inspect the parsed data and guess facts," each template declares what facts to extract:

```python
def extract_voltage_divider_facts(parsed: dict) -> dict:
    return {
        "Vout_dc": parsed["V(out)"],
        "divider_ratio": parsed["V(out)"] / {Vin_dc},
    }

def extract_rc_lowpass_facts(parsed: dict, params: dict) -> dict:
    freqs, gains = zip(*parsed["V(out)"])
    fc = find_cutoff_frequency(freqs, gains)
    passband_gain = gains[0]
    return {
        "cutoff_hz": fc,
        "passband_gain_db": passband_gain,
        "behavior": "low-pass" if fc > 0 else None,
    }
```

A registry `FACT_EXTRACTORS: dict[str, Callable]` maps topology name → extractor function. This is extended per-template, not per-simulation-type.

### 5. Fact cache: JSON files by (topology, seed)

```
└── .cache/eqa/
    ├── voltage_divider_0000002a.json
    ├── rc_lowpass_0000002a.json
    └── ...
```

Each file is `json.dumps(fact_dict)`. Cache check: `cache.get(topology, seed) → dict | None`. Cache write: `cache.put(topology, seed, facts)`.

The cache directory defaults to `.cache/eqa/` in the project root, overridable via `--cache-dir`. No LRU or expiry for now — the cache grows linearly with visible samples.

### 6. Richness scoring

After fact extraction, compute a vector:

```python
@dataclass
class RichnessScore:
    total: float  # 0.0 – 1.0
    separability: float  # how distinct facts are vs other samples
    stability: float  # numerical variance across retries
    probe_coverage: float  # are all declared probes producing data?
```

Initial implementation stubs these as 0.5 (neutral). Detailed scoring is a v2 concern once we have a batch of samples to compare against. The scoring data model exists now so the pipeline can filter on it later.

### 7. CLI: `eqa simulate`

```
eqa simulate <topology> [--seed N] [--cache-dir DIR] [--no-cache]
```

Behavior:
- Look up template, sample it, emit netlist.
- Check cache → return cached facts if hit.
- Run Xyce with retry → parse → extract facts → cache → print JSON.
- `--no-cache` skips cache read/write.

Also: `eqa simulate --all` to simulate all templates with a given seed.

### 8. Xyce subprocess interface

```python
def invoke_xyce(netlist: str, timeout_s: int = 30) -> tuple[str, int, bool]:
```

1. Write `netlist` to a temp `.cir` file
2. Run `xyce <tempfile>` via `subprocess.run` with `capture_output=True, timeout=timeout_s`
3. On timeout → `TimeoutExpired` → kill process
4. Parse output for convergence status: find "Solution by Newton" or "Convergence failure"
5. Return (stdout, returncode, converged)

## Risks / Trade-offs

- **[Risk] Xyce not installed** → CLI check at startup: `which xyce` or `xyce --version`. If missing, print "Xyce not found on PATH. Install from https://xyce.sandia.gov/". Tests mock the subprocess call.
- **[Risk] Parsing fragile text output** → we pin Xyce version and rely on its stable `.print` format. If format changes, parsers break — but this is testable with golden files.
- **[Trade-off] JSON cache vs SQLite** → JSON files are simpler and human-readable. Switch to SQLite later if >10K cache entries become a performance issue.
- **[Risk] Retry perturbation changes facts** → a 5% resistor change means the measured Vout changes. We accept this: the recorded facts match the *final* netlist that succeeded, not the original one. The seed is still recorded, and the cache key includes seed, so it's reproducible (same seed + retry = same perturbation path, since all RNG is seeded).

## Open Questions

- Should `.print` format be **Xyce raw format** (`FORMAT = RAW`) instead of default? **Answer**: no — raw format requires a separate binary parser. Default text format is parseable and human-readable. We can switch later if needed.
- Should AC/tran data be stored as numpy arrays? **Answer**: not in this change. Parsed data is Python lists of tuples. The fact extractor operates on the lists directly. numpy can be added as an optional dependency later for vectorized operations.
