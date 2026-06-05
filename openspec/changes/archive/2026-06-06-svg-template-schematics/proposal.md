## Why

The current schematic renderer (`render/schematic.py`) auto-lays out every circuit
left-to-right with ad-hoc matplotlib wire math. This algorithmic layout produces
visual quirks — disconnected leads, overlapping labels, wires that miss component
terminals — and does not generalize beyond single-loop series topologies. Because
these images are the *question stimulus* in a multimodal benchmark, layout defects
directly corrupt the dataset: a model may be asked about a node that visually looks
disconnected. We need hand-verified, topology-correct schematic layouts that
guarantee every drawn component connects exactly as the netlist says.

## What Changes

- Each circuit template gains an associated **SVG layout template**: a hand-authored,
  topology-correct schematic with named placeholder slots for component symbols,
  values, and node labels (one SVG per topology, not per sampled instance).
- Add an **SVG template registry** that maps `(family, topology)` to its template
  file and validates that the slots match the circuit's components/nodes.
- Add an **SVG-based renderer** that fills a topology's SVG template with the
  sampled circuit's component values, reference designators, and node labels, then
  rasterizes it to PNG for the existing image pipeline.
- The schematic renderer selects the SVG template path when a topology has a
  registered template, preserving deterministic, pixel-stable output.
- Ship SVG templates for the 5 MVP topologies (voltage divider, RC low-pass,
  RC high-pass, RLC band-pass, half-wave rectifier).

## Capabilities

### New Capabilities
- `svg-schematic-templates`: Per-topology hand-authored SVG layout files with named
  placeholder slots, plus a registry that resolves and validates a template against
  a `CircuitGraph`'s components and nodes.
- `svg-schematic-renderer`: Fills a resolved SVG template with sampled component
  values, designators, and node labels and rasterizes it to a deterministic PNG.

### Modified Capabilities
<!-- The prior schematic-renderer capability lives only in archived changes, not in
     openspec/specs/, so there is no active spec whose requirements change. The new
     renderer is introduced as a new capability rather than a delta. -->

## Impact

- **Code**: new `render/svg_templates.py` (registry + fill/rasterize) and SVG asset
  files under `src/electronics_qa_generator/render/svg/` (or `assets/`); modified
  `render/schematic.py` to dispatch to the SVG path; possible touch points in
  `templates/*` to declare a template id and slot mapping per topology.
- **Dependencies**: an SVG rasterizer (e.g., `cairosvg` or `resvg`/`svglib`) added
  under the existing `render` optional-dependency extra.
- **Tests**: new tests asserting slot/graph validation, value-filling correctness,
  and deterministic PNG output for the 5 MVP topologies.
- **Data**: rendered images become topology-correct; no change to netlists,
  simulation, or ground-truth answers (the invariant is preserved — rendering is
  presentation only).
