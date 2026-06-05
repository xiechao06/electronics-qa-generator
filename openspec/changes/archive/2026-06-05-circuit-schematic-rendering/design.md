## Context

The pipeline produces text-only JSON QA items today. MMMU — and any multimodal
benchmark — requires images alongside questions. The `CircuitGraph` already holds the
full component+node description of every circuit; we need a renderer that converts it
to a human-readable schematic PNG. The architecture (`docs/architecture.md` §12)
reserves a rendering stage for "schematic images, waveform plots, Bode plots." This
change implements the **schematic** renderer for the 5 MVP topologies.

## Goals / Non-Goals

**Goals:**
- Render a `CircuitGraph` as a deterministic schematic PNG using matplotlib.
- Support all 5 MVP topologies: voltage divider, RC low-pass, RC high-pass, RLC
  band-pass, half-wave rectifier (with diode symbol).
- IEEE-style symbols: resistor (zigzag), capacitor (parallel plates), inductor
  (coil), diode (triangle + bar), voltage source (circle with +/−), ground symbol.
- Engineering-notation component values (e.g., "4.7k Ω").
- Opt-in `--render` flag on `eqa emit` and `eqa questions`; output includes
  `schematic_path`.
- Deterministic output (same CircuitGraph → identical PNG every time).

**Non-Goals:**
- Waveform or Bode plots (future work). This change only handles schematics.
- Multi-loop or complex layouts (all 5 MVP topologies are single-loop series
  circuits).
- Schematic editing or user-controlled layout. Fully automatic.
- Interactive or vector output (SVG). PNG only for MVP.

## Decisions

### Decision: matplotlib for rendering
Use `matplotlib` (already listed in `pyproject.toml` under `[project.optional-
dependencies] render`). Draw symbols as `matplotlib.patches` (Polygon, FancyArrow,
Rectangle, Circle, etc.) on a Figure with a fixed grid layout.
- **Why:** Already an approved optional dependency; produces high-quality PNGs;
  allows future extension to waveform/Bode plots with the same library.
- **Alternative considered:** `schemedraw` or `circuitikz` via latex. Rejected for
  complexity and dependency weight (latex + TeX distribution).

### Decision: Fixed-axis left-to-right layout
For the 5 MVP topologies (all single-loop series circuits), layout components
horizontally with the voltage source on the left, ground at the bottom, and a
return wire completing the loop. Component positions are derived from insertion order
in `CircuitGraph.components`.
- **Why:** All 5 topologies are simple loops — a generic layout engine is overkill.
  Simple geometry rules produce readable schematics.
- **Alternative considered:** Graphviz or automatic circuit layout. Rejected for MVP
  — adds dependency and doesn't improve quality for 5 simple topologies.

### Decision: Engineering-unit formatting reuses existing code
Reuse `_fmt_resistance`, `_fmt_capacitance`, etc. from `graph/spice_emitter.py` or
extract shared formatting into a utility module. Each component label shows its
reference designator (R1, C1, L1, D1, V1) followed by the formatted value WITH UNIT
(e.g., "R1 4.7k Ω", "C1 100n F", "L1 10m H", "V1 5V DC"). The label font SHALL be
large enough (≥10pt) to be readable at the target resolution.
- **Why:** Units are essential — a schematic without units is ambiguous. Consistent
  formatting between netlist and schematic reduces confusion.
- **Alternative considered:** Separate formatting module. Rejected — the emitters are
  the single source of truth for engineering notation.

### Decision: Opt-in CLI flag with graceful degradation
`--render` is a flag on `eqa emit` and `eqa questions`. When omitted, behavior is
unchanged. When set but matplotlib is missing, a warning is printed and items emit
without `schematic_path` — the command exits 0.
- **Why:** Same pattern as `--humanize` (opt-in, best-effort, offline-safe). Keeps
  defaults unchanged and fully reproducible.

### Decision: Image output relative to output directory
Images land in `{out_dir}/render/{topology}_{id}.png`. The JSON field is
`"schematic_path": "render/voltage_divider_00000000.png"` (relative to the output
root). This matches the dataset assembler convention from the architecture doc.
- **Why:** Self-contained output directory that can be zipped/archived without broken
  paths.

## Risks / Trade-offs

- **matplotlib not installed** → Graceful import check at render time; items emit
  without `schematic_path` and log a warning.
- **Layout doesn't fit all future topologies** → scoped to 5 MVP topologies; multi-
  loop circuits will need a new layout strategy when they arrive.
- **Pixel-identical determinism** → matplotlib can produce slightly different PNGs
  across platforms (font rendering, DPI). Accept byte-level determinism on the same
  platform; for cross-platform, compare at the structure level.
- **Diode symbol complexity** → The triangle+bar is drawn with matplotlib Polygon
  patches. Tested visually on the half-wave rectifier topology.

## Migration Plan

1. Add `src/electronics_qa_generator/render/schematic.py` (render function +
   symbol drawing functions).
2. Add `--render` flag to `cli.py` for `emit` and `questions` subcommands.
3. Wire rendering into `output/emit.py` and `questions/cli_handler.py`.
4. Add tests: render each MVP topology, verify PNG dimensions, verify JSON fields.
- **Rollback:** Remove `--render` flag; no stored data changes.

## Open Questions

- Exact pixel size: 800×400 proposed; adjust based on visual testing with the
  half-wave rectifier (which has the most symbols).
- Ground symbol: standard 3-line decreasing triangle or "GND" label. Start with a
  simple label "0" and refine later.
- Should the `schematic_path` be a full filesystem path or a relative path? Relative
  (to output root) for portability; full path can be an option.
