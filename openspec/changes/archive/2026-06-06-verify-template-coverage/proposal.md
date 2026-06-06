## Why

We generate **multimodal** Q/A items where the solver sees only the **schematic
image plus the question text** — the SPICE netlist is never shown. If any fact
the answer depends on (a component value, a source level, a node label, an
analysis frequency) exists in the netlist but is absent from *both* the image and
the question, the item is silently unanswerable or ambiguous, yet our pipeline
still ships it with a "ground-truth" answer.

We recently hit this in practice: four schematics (`bjt_ce_amplifier`,
`bjt_emitter_follower`, `mosfet_cs_amplifier`, `op_amp_inverting`) omitted
components (`Cbypass`, `Rload`, `Rgnd`, `Cpole`) that the netlist contained. The
existing template validation did **not** catch it because it only checks that
*declared SVG slots* map to graph components — it never checks the reverse, that
*every* netlist component is actually drawn. We need a first-class, automated
mechanism that verifies the **question ↔ SVG ↔ netlist** triad is mutually
consistent for every topology, so the image+question always carry the full
information content of the netlist.

## What Changes

- Add a **template-triad coverage verifier** that, per topology, derives the
  canonical "information content" of the netlist (every component + value, every
  source level, every non-ground node, model names, and the analysis directive)
  and checks that each such fact is conveyed by **the rendered schematic** or
  **the question text** — never hidden in the netlist alone.
- Enforce **bidirectional** netlist↔image coverage: every graph component and
  every non-ground node MUST be represented in the rendered SVG (as a slot or
  visible label), not just the currently-checked "declared slots ⊆ components".
  **BREAKING** for any template that omits a component — it will now fail
  verification instead of silently rendering an incomplete schematic.
- Verify each **question template** against its declared `answer_keys`/program:
  every input fact the answer depends on must be derivable from information that
  is visible in the image or inlined in the question text via `{param}`
  placeholders; flag any answer-relevant fact that is invisible in both.
- Expose the verifier through the CLI (a `verify`/`verify-templates` capability)
  and as a pytest regression that runs across all registered topologies, so the
  triad is checked in CI and before batch generation.
- Produce a clear, per-topology report (PASS/FAIL with the specific missing
  component, node, or answer-relevant fact) in human-readable and JSON form.

## Capabilities

### New Capabilities
- `template-coverage-verification`: A cross-artifact checker that verifies, for
  each topology, that the question template, SVG template, and netlist/graph are
  mutually consistent — specifically that the union of (schematic image +
  question text) conveys every netlist fact the answer depends on. Includes the
  netlist-fact model, the coverage rules, the report format, the CLI surface, and
  the all-topologies regression test.

### Modified Capabilities
- `svg-schematic-templates`: Strengthen the registry's template/graph validation
  from one-directional ("declared slots match components") to **bidirectional
  coverage** — every graph component and every non-ground node MUST appear in the
  template, so an incomplete schematic is rejected before any PNG is produced.

## Impact

- **Code**: `render/svg_templates.py` (registry `_validate` → full coverage),
  a new verifier module under `validation/` (e.g. `template_coverage.py`),
  `cli.py` / validation `cli_handler.py` (new subcommand surface),
  and the question/extraction metadata it reads (`questions/templates.py`,
  `questions/programs.py`, `questions/compute.py` units/keys).
- **Tests**: new `tests/` coverage for the verifier plus an all-topologies
  regression (generalizing the schematic-completeness test already added).
- **Process**: verification becomes a gate that should run before batch
  generation; failing topologies block shipping QA items.
- **No new runtime dependencies**; reuses the existing graph, registry, and
  question-template registries. Xyce is **not** required (this is a static,
  template-level check that operates on sampled graphs, not simulation output).
