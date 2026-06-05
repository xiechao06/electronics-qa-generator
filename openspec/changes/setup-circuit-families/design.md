## Context

The pipeline's template library is currently a stub (`templates/__init__.py` with a docstring). The architecture doc (docs/architecture.md) and plan (docs/plan.md) define what templates must provide: topology graphs, parameter ranges, simulation types, measurable outputs, rejection rules, and a `sample()` method. The first implementation needs concrete decisions about base classes, parameter distributions, netlist emission, and file organization.

Python 3.14 is the target, so `abc.ABC` and modern typing are available. No external dependencies (numpy) are needed for templates themselves — `random.Random` with explicit seeds suffices.

## Goals / Non-Goals

**Goals:**
- A base `CircuitTemplate` class with a clear `sample()` contract returning `CircuitRecord`
- A parameter distribution system supporting uniform, log-uniform, and choice distributions with deterministic seeding
- Netlist emission helpers that bind sampled parameters into valid Xyce/SPICE syntax
- Five MVP circuit templates with independently verifiable sample output
- Every `sample()` call must be reproducible given the same seed

**Non-Goals:**
- Simulation execution (Xyce integration) — that's the `simulation/` stage
- Fact extraction or question generation — those are downstream stages
- Complex rejection rules — initial templates produce valid circuits deterministically
- Large families (op-amp, BJT, MOSFET) — out of scope per MVP plan
- Counterfactual variants — add later

## Decisions

### 1. Base class: `ABC` with abstract `sample()`

Use `abc.ABC` + `@abstractmethod` rather than a `Protocol`. Templates need shared state (family, topology name, parameter distributions) and shared helper methods (netlist emission). An ABC naturally supports both. Protocols would be unnecessarily loose for a pipeline stage where every template must conform.

```python
class CircuitTemplate(ABC):
    family: str          # e.g. "passive", "diode"
    topology: str        # e.g. "rc_lowpass"

    @abstractmethod
    def sample(self, seed: int | None = None) -> CircuitRecord: ...
```

Every concrete template stores its parameter distributions as instance attributes and implements `sample()`.

### 2. Parameter distributions: simple classes, seeded `random.Random`

Three distribution types suffice for MVP:

| Distribution | Config | Example |
|---|---|---|
| `Uniform` | `(min, max)` | `Uniform(1e3, 1e6)` → R = 10kΩ |
| `LogUniform` | `(min, max)` | `LogUniform(1e-10, 1e-6)` → C = 4.7nF |
| `Choice` | `[values]` | `Choice([1e-9, 1e-8, 1e-7])` → select one E-series value |

Each distribution class has a `sample(rng: random.Random) -> float` method. The template creates a `random.Random(seed)` and passes it to every distribution's `sample()`. This gives full reproducibility without global state.

**Alternative considered:** scipy.stats distributions. Rejected — adds a heavy dependency for what amounts to 20 lines of math. `random.Random` is sufficient.

Not using numpy yet — `random.Random` produces correct distributions and numpy is an optional extra (`sim` group). Templates should stay dependency-free.

### 3. Netlist generation: template strings with placeholder substitution

Use Python f-string/template substitution over SPICE netlist templates stored as class attributes. Example:

```python
_netlist_op = """* RC low-pass (operating point)
Vin in 0 DC {Vin_dc}
R1 in out {R1_ohm:.1f}
C1 out 0 {C1_f:.6e}
.op
.print op V(out)
.end"""
```

Bind with `_netlist.format(**params)`. This is simpler than building an AST of SPICE elements, and the templates are trivially readable. Each template class can have multiple netlist templates for different simulation types (`.op`, `.ac`, `.tran`).

**Alternative considered:** a SPICE netlist AST with element objects. Rejected for MVP — premature abstraction when only 5 circuits exist.

### 4. CircuitRecord integration

Templates populate these fields on the `CircuitRecord` they return:

| Field | Populated by | Example |
|---|---|---|
| `id` | Format string: `{topology}_{seed:04x}` | `rc_lowpass_a3f2` |
| `family` | Class attribute | `"passive"` |
| `topology` | Class attribute | `"rc_lowpass"` |
| `difficulty` | Parameter (default 1) | `1` |
| `parameters` | Sampled values dict | `{"R1_ohm": 18200, "C1_f": 4.7e-9}` |
| `netlist` | Bound netlist string | `"* RC low-pass\n..."` |
| `simulation` | `SimulationConfig` | `SimulationConfig(type="ac", tool="Xyce", params=...)` |
| `probes` | Class attribute | `["V(out)"]` |

The downstream `netlist/` stage will take this record and potentially add sweep-specific netlists. For now the template emits exactly one netlist.

### 5. File organization: one module per circuit family

```
src/electronics_qa_generator/templates/
  __init__.py          # exports all templates
  base.py              # CircuitTemplate ABC, Distribution classes
  netlist_helpers.py   # unit formatting, value formatting helpers
  passive.py           # VoltageDivider, RCLowPass, RCHighPass, RLCBandPass
  rectifier.py         # HalfWaveRectifier
```

One module per **family** (passive, rectifier), not per individual circuit. Each file is small enough for now, and families share simulation types and netlist patterns.

**Alternative considered:** one file per circuit. Rejected — 5 files with ~40 lines each creates unnecessary navigation overhead at MVP scale.

### 6. Parameter ranges: E-series values for components

Component values are sampled from standard ranges to produce realistic circuits:

- Resistors: E12 series (1.0, 1.2, 1.5, … × decade multiplier) between 100Ω and 1MΩ
- Capacitors: E6 series (1.0, 1.5, 2.2, … × decade multiplier) between 10pF and 100μF
- Inductors: selected values between 1mH and 100mH

This avoids arbitrary 6-decimal values like `R1 = 18.2347kΩ` that no real circuit would use, while still producing diverse parameter combinations.

**Alternative considered:** continuous log-uniform sampling. Rejected — produces values unrealistic for a textbook/exam-style benchmark.

## Risks / Trade-offs

- **[Risk] E-series constraint limits parameter diversity** → **Mitigation**: 5 circuits × multiple decades of E-series values still produces thousands of unique parameterizations. The diversity comes from cross-circuit combinations, not arbitrary precision.
- **[Risk] No rejection rules yet** — template always produces a "valid" circuit, but some parameter combinations might produce degenerate simulation results (gain = 0, cutoff outside sweep range, etc.). → **Mitigation**: That's the quality filter's job (downstream `validation/` stage). Templates only guarantee syntactic validity of the netlist.
- **[Risk] `random.Random` is not cryptographically strong** → Not a concern for synthetic dataset generation; reproducibility is the goal.
- **[Trade-off] Hard-coded netlist templates** are less flexible than an AST. → Acceptable for MVP. When we add op-amp/BJT families with subcircuit libraries, we'll revisit.

## Open Questions

- Exact E-series values to use for inductors (less standardized than R and C). Start with `[1e-3, 2.2e-3, 4.7e-3, 1e-2, 2.2e-2, 4.7e-2, 1e-1]` (H) and adjust based on simulation behavior.
- Should netlist emission stay in the `templates/` package or move to `netlist/writer.py`? The proposal places it here as a helper; if it grows, it can migrate.
