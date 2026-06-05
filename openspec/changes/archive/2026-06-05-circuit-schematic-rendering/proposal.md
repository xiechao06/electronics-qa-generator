## Why

The pipeline currently produces QA items in JSON with text only. A multimodal
benchmark like MMMU requires images — circuits are visual by nature and questions
like "find the cutoff frequency of the filter shown" are meaningless without a
schematic the model can see. To make this a true multimodal dataset, we need to render
**schematic diagrams** from the `CircuitGraph` and include them alongside the generated
questions.

## What Changes

- Add a rendering stage in the existing (stub) `render/` subpackage that produces
  schematic PNG images from `CircuitGraph` objects using `matplotlib` (already listed
  as an optional `render` dependency).
- Render standard IEEE circuit symbols: resistor (zigzag), capacitor (parallel
  plates), inductor (coil), diode (triangle + bar), voltage source (circle with ±),
  with component labels and values using engineering notation.
- Auto-layout components in a left-to-right flow along one axis (single loop for all
  five MVP topologies), placing components and nodes using simple geometric rules.
- Wire the renderer into `eqa questions --render` (opt-in flag) and `eqa emit` with a
  `--render` flag, producing a PNG file per circuit.
- Extend the `QAItem` and output JSON to include `schematic_path` pointing to the
  rendered image.

## Capabilities

### New Capabilities
- `schematic-renderer`: Render a `CircuitGraph` as a schematic PNG image using
  matplotlib, supporting all 5 MVP topologies (voltage-divider, RC low-pass/high-pass,
  RLC band-pass, half-wave rectifier). Covers component symbols, auto-layout,
  engineering-unit value labels, and node labels.
- `render-cli`: The `--render` flag on both `eqa emit` and `eqa questions` that
  produces schematic images alongside the netlist/QA output. Covers output paths,
  image-q pairing in JSON output, and the flag's opt-in nature.

### Modified Capabilities
<!-- No existing spec changes. -->

## Impact

- **Code**: `src/electronics_qa_generator/render/` (new `schematic.py`, `symbols.py`,
  `layout.py`); `src/electronics_qa_generator/output/emit.py` and
  `questions/cli_handler.py` (+ `--render` flag + image generation call);
  `cli.py` (+ `--render` arg).
- **Dependencies**: Requires `matplotlib>=3.9` (already in `[project.optional-dependencies] render`). Users install with `uv sync --extra render`.
- **Output**: One `.png` per circuit, referenced by relative path in the JSON output
  via a new `schematic_path` field.
- **Invariant**: Rendering is purely visual — it reads the `CircuitGraph` deterministically and never touches answer computation.
