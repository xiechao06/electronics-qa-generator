## Context

Five circuit templates exist (voltage divider, RC low-pass, RC high-pass, RLC band-pass, half-wave rectifier), each emitting a `CircuitRecord` with a `netlist` string built via `str.format()`. The templates are simple enough that the string approach works, but adding transistor amplifiers, op-amp circuits, or topology perturbations will make manual string construction error-prone and opaque. Python 3.14, stdlib only, `uv` build tool.

## Goals / Non-Goals

**Goals:**
- Create `CircuitGraph` and `Component` as lightweight `@dataclass` structures in a new `graph/` subpackage.
- Provide `to_spice(simulation: SimulationConfig) -> str` to emit Xyce netlists from a graph.
- Provide `validate() -> list[str]` returning an empty list on success or error strings for floating nodes, duplicate names, etc.
- Port all 5 existing templates to use the graph API with **byte-identical netlist output** — same node names, same component ordering, same comment lines, same `.end`.
- Keep `CircuitRecord` and `CircuitTemplate` unchanged — `netlist` is still populated as a string from `graph.to_spice()`.

**Non-Goals:**
- Netlist *parsing* (string → graph). The graph is the source of truth; we don't need to parse existing netlists.
- A full circuit DSL or visual layout — just nodes + typed components.
- Changing component value distributions, simulation types, or probe declarations — those stay in the template subclass logic.
- Supporting non-SPICE serialization formats (JSON schema, schematic SVG) — those are future concerns; only `to_spice()` for now.

## Decisions

### 1. CircuitGraph as flat ordered list, not adjacency matrix

```python
@dataclass
class Component:
    name: str         # "R1", "C1", "D1", "Vin"
    kind: str         # "resistor", "capacitor", "inductor", "vsource", "diode"
    pos: str          # positive/connected node name
    neg: str          # negative/reference node name
    params: dict = field(default_factory=dict)  # {"value": 1000} or {"dc": 5}
    comment: str | None = None  # optional per-component comment line

@dataclass  
class CircuitGraph:
    nodes: dict[str, int]       # node name → index (ground is always node 0)
    components: list[Component]  # ordered — this IS the netlist order
```

**Why flat list:** SPICE netlists are inherently ordered lists of component lines. The order matters for readability and stability. An adjacency matrix or node-edge graph would be more computationally useful for traversals, but harder to keep stable ordering when serializing. We choose ordered list for now; adjacency queries can be derived from `components`.

**Why name-index node map:** Xyce expects nodes to be named (not numbered), so `nodes` maps "in" → 0, "out" → 1, etc. This lets `to_spice()` validate that every component references existing nodes and that ground (node 0) is present.

### 2. Graph construction via methods, not direct dataclass manipulation

```python
class CircuitGraph:
    def add_resistor(self, name: str, pos: str, neg: str, value_ohm: float, *, comment: str | None = None) -> None
    def add_capacitor(self, name: str, pos: str, neg: str, value_f: float, *, comment: str | None = None) -> None
    def add_inductor(self, name: str, pos: str, neg: str, value_h: float, *, comment: str | None = None) -> None
    def add_voltage_source(self, name: str, pos: str, neg: str, *, dc: float | None = None, ac: float | None = None, sin: dict | None = None) -> None
    def add_diode(self, name: str, pos: str, neg: str, model: str = "1N4148") -> None
```

These methods handle node registration and component type normalization internally. Templates never construct `Component` or `CircuitGraph.nodes` directly — they only call `add_*` methods. This ensures:
- All node names are registered before any component references them.
- Component `kind` strings are consistent (always "resistor", not "R" or "r").
- A single ground node "0" is always present.

### 3. `to_spice()` emits Xyce netlist in a consistent order

```python
def to_spice(self, simulation: SimulationConfig) -> str:
```

Emission order:
1. Per-component comment lines (if `component.comment` is set)
2. Component instances grouped by kind in canonical order: vsources → resistors → capacitors → inductors → diodes
3. Simulation control card (`.op` / `.ac` / `.tran` / `.dc`)
4. `.print` line(s) according to simulation type
5. `.end`

**Why group by kind, not insertion order:** Netlist ordering by kind is more readable and conventional. SPICE does not care about order within a section. But we MUST produce byte-identical output for existing templates to keep tests green — so the emitter must match the exact byte order of the current string templates.

### 4. Component value formatting lives in `to_spice()`, not in templates

Currently templates call `_format_resistance(r1)` to pretty-print "6.8k". With graph API:
- `add_resistor(name, pos, neg, value_ohm=6800.0)` stores the numeric value.
- `to_spice()` formats it: 6800.0 → "6.8k", 100 → "100", 1e6 → "1Meg".
- Same for capacitors (1e-7 → "100n"), inductors (0.01 → "10m"), and voltages.

This means `netlist_helpers.py` functions move from template call sites into the graph emitter, and template code only passes floats.

### 5. Template porting strategy: byte-identical output

Each template's `sample()` method is rewritten to:
1. Create `CircuitGraph()` 
2. Call `graph.add_*()` for each component
3. Call `graph.to_spice(simulation_config)`
4. Return `CircuitRecord(netlist=netlist, ...)` where netlist is the `to_spice()` output

The **same node names** and **same component ordering** must be preserved. For example, `VoltageDivider` currently emits:

```
* Voltage divider — DC operating point
Vin in 0 DC {Vin_val}
R1 in out {R1_val}
R2 out 0 {R2_val}
.op
.print op V(out)
.end
```

The graph version must produce **exactly** this string (with values filled in), byte-for-byte. Comments are passed via `comment=` on the first component or a `header_comment` on the graph.

### 6. `validate()` as a pre-send guard

```python
def validate(self) -> list[str]:
```

Returns empty list on success, or list of error strings. Checks:
- Every component references nodes that exist in `self.nodes`
- No duplicate component names
- At least one voltage/current source exists
- No floating nodes (nodes with exactly one connection, excluding ground)
- Ground node "0" exists

This is called before `to_spice()` inside template code — and later, in the simulation stage, before invoking Xyce.

## Risks / Trade-offs

- **[Risk] Byte-identical output is fragile** — the emitter must match current string templates exactly. **Mitigation**: existing template tests serve as golden-file tests; we keep them and add new graph-specific tests separately.
- **[Trade-off] Flat ordered list over true graph** — we can't do efficient path queries or cycle detection. **Acceptable for now**: these aren't needed yet; adjacency can be derived from `components` when needed. A true graph library can be introduced later without changing the `add_*` API.
- **[Risk] Diode model string hardcoded** — half-wave rectifier uses "1N4148" hardcoded in the emitter. **Mitigation**: the model string is a parameter passed to `add_diode(name, pos, neg, model="1N4148")` — templates control it.
- **[Trade-off] Ground is hardcoded as "0"** — this is the Xyce convention and unlikely to change. If needed, make it a graph-level attribute.

## Open Questions

- Should `CircuitGraph` live in `templates/graph.py` or a new top-level `graph/` subpackage? **Decision**: new `src/electronics_qa_generator/graph/` subpackage — other pipeline stages (simulation, QA generation) will also need graph access, so it shouldn't be nested under templates.
- Should `to_spice()` accept a `SimulationConfig` as a method arg or be stored on the graph? **Decision**: method arg — the same graph can be simulated with different configs (op, ac, tran), so the config belongs at emission time, not construction time.
