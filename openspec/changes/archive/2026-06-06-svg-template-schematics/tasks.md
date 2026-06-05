## 1. Dependencies & Scaffolding

- [x] 1.1 Add `cairosvg` to the `render` optional-dependency extra in `pyproject.toml` and run `uv sync --extra render`
- [x] 1.2 Create the package data directory `src/electronics_qa_generator/render/svg/` and ensure SVG assets are included in the wheel (package-data / build config)
- [x] 1.3 Create empty modules `render/svg_templates.py` (registry + slot model) and `render/svg_render.py` (fill + rasterize), exported from `render/__init__.py`

## 2. SVG Template Registry & Slot Model

- [x] 2.1 Define a slot model that enumerates value slots (keyed by reference designator) and node-label slots (keyed by node name) parsed from an SVG by stable element ids (e.g., `slot-R1`, `slot-node-out`)
- [x] 2.2 Implement loading an SVG template via `importlib.resources` so it resolves independent of CWD
- [x] 2.3 Implement a registry mapping `(family, topology)` → template file with `resolve(graph)` and `has_template(graph)`
- [x] 2.4 Implement `validate(template, graph)` that checks slots match the graph's components and nodes, raising a clear error naming the missing/extra slot

## 3. Author MVP SVG Templates

- [x] 3.1 Author and commit a topology-correct SVG template with named slots for `voltage_divider`
- [x] 3.2 Author and commit SVG templates for `rc_lowpass` and `rc_highpass`
- [x] 3.3 Author and commit an SVG template for `rlc_bandpass`
- [x] 3.4 Author and commit an SVG template for `half_wave_rectifier` (diode + load)
- [x] 3.5 Register all 5 templates in the registry

## 4. Fill & Rasterize

- [x] 4.1 Implement `fill_template(graph, template)` that populates value slots using the existing `render/format.py` `format_component_label`, and node slots with graph node names
- [x] 4.2 Implement rasterization of the filled SVG to PNG via `cairosvg` at a fixed DPI/canvas size, white background / black foreground, written to a caller-specified path
- [x] 4.3 Ensure repeated renders of the same graph produce pixel-identical PNGs (fixed settings, no timestamps/random ids)

## 5. Renderer Dispatch

- [x] 5.1 Update `render_schematic` to dispatch to the SVG path when `registry.has_template(graph)` is true, keeping the existing signature
- [x] 5.2 Preserve the existing matplotlib layout as the fallback for unregistered topologies
- [x] 5.3 Lazily import `cairosvg` inside the SVG path so the base install (without the `render` extra) still works for the fallback

## 6. Tests

- [x] 6.1 Test registry resolution: known topology resolves a template; unknown topology reports no template
- [x] 6.2 Test slot/graph validation rejects mismatched slots with a clear error
- [x] 6.3 Test `fill_template` populates value and node slots with correctly formatted labels and leaves netlist/sim/probes unchanged
- [x] 6.4 Test PNG is produced at the requested path and is a valid image for each of the 5 MVP topologies
- [x] 6.5 Test two renders of the same graph are pixel-identical
- [x] 6.6 Test `render_schematic` falls back to matplotlib for an unregistered topology

## 7. Verification

- [x] 7.1 Run `uv run pytest` and `uv run ruff check .` and `uv run ruff format .`; fix any issues
- [x] 7.2 Visually inspect rendered PNGs for all 5 MVP topologies to confirm no disconnected components or label overlap
