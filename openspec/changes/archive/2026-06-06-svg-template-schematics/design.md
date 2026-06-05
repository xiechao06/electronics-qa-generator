## Context

Rendered schematics are the *visual stimulus* of the benchmark, so layout defects
become dataset defects. The current renderer (`render/schematic.py`) computes wire
geometry algorithmically for a single-loop, left-to-right layout. This produces
quirks — disconnected leads, label overlap, wires that miss terminals — and does not
generalize beyond series topologies. The proposal introduces hand-authored,
topology-correct SVG templates (one per topology) that the renderer fills with each
sampled circuit's values and rasterizes to PNG.

Relevant current state:

- `templates/*` build a `CircuitGraph` and emit netlists; `graph/models.py` holds
  components/nodes; `render/schematic.py` rasterizes via matplotlib; `render/format.py`
  already does engineering-unit label formatting; `render/symbols.py` draws IEEE
  symbols. The 5 MVP topologies are voltage divider, RC low-pass, RC high-pass,
  RLC band-pass, half-wave rectifier.

Project invariant: rendering is presentation only. This change must not touch
netlists, simulation, or answer derivation.

## Goals / Non-Goals

**Goals:**
- Topology-correct schematics whose wires always connect to the right terminals.
- One reusable SVG template per topology, filled per sampled instance.
- Deterministic, pixel-stable PNG output, reusing existing label formatting.
- No change to the public `render_schematic` signature or the render CLI.
- Graceful fallback to the existing matplotlib path for unregistered topologies.

**Non-Goals:**
- Auto-routing or auto-placing arbitrary netlists (templates are hand-authored).
- Per-instance SVG authoring (templates are per topology, not per sample).
- New question types, families, or any change to ground-truth computation.
- A general schematic editor or interactive layout tooling.

## Decisions

**1. Hand-authored SVG per topology with named slots (vs. programmatic SVG).**
Authoring the layout once by hand guarantees correct connectivity, which is the whole
point. Slots are marked by stable ids (e.g., `id="slot-R1"`, `id="slot-node-out"`) so
the filler can locate and replace placeholder text/symbols. Alternative — generating
SVG programmatically — reintroduces the same geometry-math fragility we are removing.

**2. Slot model: text slots keyed by reference designator and node name.**
Each template declares value slots keyed by designator (`R1`, `C1`, `Vin`) and node
slots keyed by node name (`in`, `out`, `0`). The registry validates that the template's
slot set matches the `CircuitGraph`'s components and nodes, failing loudly on mismatch.
This keeps templates and graphs in lockstep as families evolve.

**3. Registry maps `(family, topology)` → template file.**
A small registry module resolves templates and exposes `has_template(graph)` so the
renderer can dispatch. Keeping it data-driven (a dict plus asset files) avoids
hard-coding per-topology logic in the renderer.

**4. Reuse `render/format.py` for labels.**
The filler calls the existing `format_component_label` so SVG labels are identical to
the matplotlib path and the rest of the pipeline. No second formatting code path.

**5. Rasterizer: `cairosvg` (vs. `resvg`/`svglib`).**
`cairosvg` is pure-Python-friendly, deterministic at a fixed DPI, and easy to add under
the existing `render` optional-dependency extra. `resvg` needs a native binary;
`svglib`+`reportlab` has weaker SVG feature coverage. Add the dep to the `render` extra,
not base dependencies.

**6. Dispatch with fallback in `render_schematic`.**
`render_schematic` checks the registry: if a template exists, render via the SVG path;
otherwise use today's matplotlib layout. This lets the 5 MVP topologies adopt SVG while
keeping the function signature and CLI stable, and avoids a flag day.

**7. Asset location.**
SVG templates live under `src/electronics_qa_generator/render/svg/` and are packaged
with the wheel, so they resolve via `importlib.resources` regardless of CWD.

## Risks / Trade-offs

- **New native-ish dependency (`cairosvg`/cairo)** → Confine it to the `render` extra
  and import lazily inside the renderer; fallback path keeps base install working.
- **Slot/graph drift as topologies change** → Registry validation fails loudly with the
  offending slot name; a test per MVP topology asserts slot↔graph consistency.
- **Determinism across environments** → Pin DPI and canvas size; assert two-render
  pixel-identity in tests. Cross-machine identity is best-effort (font rendering); keep
  text minimal and rely on the same fixed rasterizer settings.
- **Authoring effort per new topology** → Accepted cost; correctness of the stimulus is
  worth more than auto-layout convenience, and templates are authored once.
- **Font availability** → Prefer a single widely-available font (or paths-to-text) to
  reduce environment variance.

## Migration Plan

1. Add `cairosvg` to the `render` optional-dependency extra; add registry + filler
   modules with no wiring yet.
2. Author and commit SVG templates for the 5 MVP topologies; register them.
3. Wire `render_schematic` to dispatch to the SVG path when a template is registered,
   keeping the matplotlib fallback.
4. Validate rendered images for all MVP topologies; compare against current output for
   connectivity correctness.
5. Rollback: remove registrations (or the registry returns no template) and the renderer
   reverts to the matplotlib path automatically.

## Open Questions

- Should node `0` always render as a ground symbol slot rather than a text label?
- Do we want a `--renderer {svg,matplotlib}` override on the render CLI for debugging,
  or keep dispatch fully automatic?
- Is cross-machine pixel identity required, or is single-machine determinism sufficient
  for dataset reproducibility?
