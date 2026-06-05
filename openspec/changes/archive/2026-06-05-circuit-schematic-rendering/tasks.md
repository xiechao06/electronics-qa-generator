## 1. Circuit symbol drawing utilities

- [x] 1.1 Add `src/electronics_qa_generator/render/symbols.py` with matplotlib-backed
  functions: `draw_resistor(ax, x, y, angle)`, `draw_capacitor(ax, x, y, angle)`,
  `draw_inductor(ax, x, y, angle)`, `draw_diode(ax, x, y, angle)`,
  `draw_voltage_source(ax, x, y, angle)`, `draw_ground(ax, x, y)`. Each draws at
  the given position with default orientation (horizontal = 0°, vertical = 90°).
- [x] 1.2 Add symbol-size constants (e.g., `SYMBOL_LENGTH=60` pixels equivalent in
  data coords) so all symbols are visually balanced.

## 2. Engineering-unit label formatting

- [x] 2.1 Extract or reuse shared formatting functions (`_fmt_resistance`,
  `_fmt_capacitance`, `_fmt_inductance`, `_fmt_voltage`, `_fmt_frequency`) from
  `graph/spice_emitter.py`. Each component label MUST show the reference designator
  AND formatted value WITH unit suffix (e.g., "R1 4.7k Ω", "C1 100n F",
  "L1 10m H", "V1 5V DC"). Labels use ≥10pt font for readability.

## 3. Schematic layout and rendering

- [x] 3.1 Add `src/electronics_qa_generator/render/schematic.py` with
  `render_schematic(graph: CircuitGraph, output_path: Path, *, width: int = 800,
  height: int = 400) -> None` that lays out components left-to-right along a
  horizontal series path with the voltage source on the left, ground symbol at the
  bottom, a return wire closing the loop, and node labels at connection points.
- [x] 3.2 Implement the layout engine: iterate `graph.components` in order, placing
  each horizontally with fixed spacing; the voltage source and first component span
  top-to-bottom; return wire runs horizontally at bottom of figure; ground symbol
  anchored at the bottom-left.
- [x] 3.3 Ensure deterministic output: seed matplotlib's random state, use fixed
  figure DPI (100), fixed font, and fixed axis limits. Same CircuitGraph → identical
  PNG.

## 4. Rendering tests

- [x] 4.1 Add `tests/test_render/test_symbols.py` — verify each symbol function
  draws the expected matplotlib patches (count, type, bounding box).
- [x] 4.2 Add `tests/test_render/test_schematic.py` — render each of the 5 MVP
  topologies via a helper that builds a CircuitGraph; verify each produces a valid
  PNG, correct dimensions (≥800×400), white background, non-empty pixel content.
- [x] 4.3 Add a determinism test: render the same CircuitGraph twice and assert the
  PNG bytes are identical.
- [x] 4.4 Add a label-formatting test: verify resistor 4700 → "4.7k Ω" (with unit),
  capacitor 1e-7 → "100n F", inductor 0.01 → "10m H"; each label includes both
  the reference designator and the formatted value+unit.

## 5. CLI integration

- [x] 5.1 Add `--render` flag to `eqa emit` and `eqa questions` subparsers in `cli.py`,
  plus an optional `--out` argument defaulting to `out/`.
- [x] 5.2 In `output/emit.py`, when `--render` is set, call `render_schematic` after
  emitting the record; include `schematic_path` in the JSON output.
- [x] 5.3 In `questions/cli_handler.py`, when `--render` is set, render the schematic
  before (or alongside) QA generation and include `schematic_path` in each QA item's
  emitted dict.
- [x] 5.4 Graceful degradation: if matplotlib is not importable, log a warning and
  emit items without `schematic_path`; exit 0.
- [x] 5.5 Add CLI tests: `--render` flag produces PNG and includes path in output;
  without `--render` output is unchanged; missing matplotlib warns and exits 0.

## 6. Docs and validation

- [x] 6.1 Document the `--render` flag and `uv sync --extra render` setup in
  `README.md`.
- [x] 6.2 Add `tests/test_render/__init__.py`.
- [x] 6.3 Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`; all
  must pass before marking the change ready to archive.
