## Context

QA items are multimodal: a solver sees a **schematic PNG** and a **question
string**, and must produce the numeric/label answer. The SPICE netlist is the
source of truth for the answer but is never shown to the solver. The pipeline
already enforces the core invariant "simulation establishes facts, code derives
answers, the LLM only paraphrases." This change adds a complementary invariant on
the *input* side: **the (image + question) pair must carry all netlist
information the answer depends on.**

Current state of the three artifacts:

- **Netlist/graph** — produced by `CircuitTemplate.sample(seed)` → `CircuitRecord`
  with a `CircuitGraph` (`graph/models.py`). Components carry `name`, `kind`,
  `pos`, `neg`, and `params` (values, model names); the graph exposes
  `non_ground_nodes` and `params`, and emits the SPICE netlist + analysis
  directive.
- **SVG template** — one hand-authored file per topology under
  `render/svg/<topology>.svg`, resolved by `render/svg_templates.py`. The
  registry's `_validate` currently checks only **declared slots ⊆ graph
  components/nodes** (one-directional). Plain-text labels (e.g. `Cin`, `Cout`)
  are not slots, and missing components are invisible to validation — the exact
  gap that let `Cbypass`/`Rload`/`Rgnd`/`Cpole` ship undrawn.
- **Question templates** — `questions/templates.py`, each with a CLEVR-style
  `program`, `answer_keys`, and a `question_template` string whose `{param}`
  placeholders are filled from `params ∪ facts` in `questions/generator.py`.
  A question conveys a fact either by **inlining** it (`R1 = {R1_ohm} Ω`) or by
  **deferring to the image** ("shown in the schematic").

A schematic-completeness pytest was already added as a stopgap. This change turns
that idea into a first-class, reusable verifier covering the full triad, and
upgrades the registry validation to be bidirectional so incomplete schematics
fail at render time too.

## Goals / Non-Goals

**Goals:**

- Derive a deterministic **netlist fact set** per sampled topology (components +
  values, sources, non-ground nodes, model names, analysis directive).
- Verify **netlist → image** coverage: every component and node is drawn.
- Verify **netlist → (image ∪ question)** coverage: every *answer-relevant* fact
  is visible in the schematic or stated in the question text.
- Surface results as a per-topology PASS/FAIL report (human + JSON), wired into
  the `eqa` CLI (non-zero exit on failure) and an all-topologies pytest.
- Strengthen `TemplateRegistry._validate` to bidirectional coverage so renders of
  incomplete templates are rejected.

**Non-Goals:**

- No VLM/LLM judgment of the *image*. Coverage is checked structurally
  (designators/nodes present in the rendered SVG text and labels), not by
  "reading" pixels. The existing opt-in Ollama visual checks remain separate.
- No Xyce/simulation dependency — verification operates on sampled graphs and the
  static template/question registries.
- Not a per-item validator. This checks **templates** (per topology), which is
  where the structural guarantees live; per-seed sampling does not change which
  designators/nodes exist.
- No redesign of the question DSL or the SVG slot conventions.

## Decisions

### 1. A dedicated verifier module, not bolted onto `validate`

Add `validation/template_coverage.py` exposing a pure function, e.g.
`verify_topology(template, registry) -> TopologyReport` and
`verify_all() -> CoverageReport`. Rationale: the triad check is **template-level**
and static, distinct from `eqa validate`'s per-item static checks. Keeping it a
standalone module makes it reusable from both the CLI and pytest, and keeps the
"image+question covers netlist" invariant in one auditable place.

*Alternative considered:* fold it into `validation/checks.py` as another per-item
check. Rejected — it would re-run redundantly per seed and conflates item-level
and template-level concerns.

### 2. Netlist fact set derived from the graph, reusing the renderer's view

Build the fact set directly from `CircuitGraph`: one entry per component
(`designator`, `value/params`), per non-ground node, per device `model`, plus the
analysis directive. For **image coverage**, reuse the existing render path
(`fill_template` + the rendered SVG string) and check that each designator/node
string is present — generalizing the stopgap test. This keeps "what counts as
shown" identical to what the registry validates and what actually renders.

*Alternative considered:* parse the PNG. Rejected — brittle and unnecessary; the
SVG text already encodes every label deterministically.

### 3. Question coverage keys off `answer_keys` + program inputs

For each question template, the **answer-relevant facts** are the `answer_keys`
plus any `read_fact`/`read_param` inputs in the `program`. A fact is "conveyed by
the question" if its corresponding `{param}` placeholder appears in
`question_template`, and "conveyed by the image" if the underlying component/node
is drawn. Map derived facts (e.g. `Vout_dc`, `cutoff_hz`) back to their governing
components/params via a small, explicit dependency table per topology so we don't
demand that a *computed* quantity be printed — only that its **inputs** are
visible. Rationale: matches how a human solves it (read R/C/V from the figure,
compute the cutoff). Keep the table explicit and reviewed, never inferred by an
LLM.

*Alternative considered:* require every `answer_key` literally present in image or
text. Rejected — derived answers (the whole point of "derived" questions) would
falsely fail; we must check *inputs*, not *outputs*.

### 4. Bidirectional registry validation (the BREAKING piece)

Extend `_validate` so that, in addition to "declared slots ⊆ components/nodes",
it asserts "components ⊆ rendered-representation" and "non-ground nodes ⊆
rendered-representation", where representation includes plain-text labels (not
only `slot-*` ids). Components and nodes will be detected by presence of their
name in the SVG text. Rationale: the renderer is the natural choke point; failing
here prevents any incomplete PNG regardless of who calls it. This is BREAKING for
any template that omits a part — but all current templates were just fixed, so the
suite is green.

### 5. CLI surface and exit code

Expose as an `eqa` subcommand (e.g. `eqa verify-templates`, JSON via `--json`)
that runs `verify_all()` and exits non-zero on any FAIL, so it can gate batch
generation. Rationale: cheap, fast, no Xyce, ideal as a pre-flight before
`scripts/batch_generate.py`.

## Risks / Trade-offs

- **[Substring false-positives]** Checking a designator by substring (e.g. `R1`
  matching `R12`) could over-credit coverage → Mitigation: match against the
  template's enumerated slot ids and word-boundary-delimited label text, and add
  targeted tests for shared prefixes.
- **[Dependency table drift]** The per-topology fact→inputs table can fall out of
  sync as questions evolve → Mitigation: keep it adjacent to the question
  templates, fail closed (unknown fact ⇒ require its own visibility), and cover it
  with the regression test.
- **[BREAKING validation]** Stricter `_validate` could reject a future template
  mid-development → Mitigation: error messages name the exact missing
  designator/node; the verifier CLI gives the same signal earlier and in batch.
- **[Structural-not-semantic]** A label can be present but visually misplaced;
  structural coverage won't catch that → Mitigation: out of scope here; the opt-in
  VLM `topology_match`/`label_visibility` checks remain the semantic backstop.

## Migration Plan

1. Land `validation/template_coverage.py` + report types and the all-topologies
   pytest (already green given the recent schematic fixes).
2. Tighten `TemplateRegistry._validate` to bidirectional coverage; run the full
   suite to confirm no regressions.
3. Add the `eqa` subcommand and document it in `AGENTS.md`/`README.md` as a
   pre-flight before batch generation.
4. Rollback: the verifier and CLI are additive; reverting the `_validate` change
   restores the prior one-directional behavior without data loss.

## Open Questions

- Should the verifier also assert that **inlined** question values match the
  schematic (cross-check duplicated facts agree), or is presence-coverage enough
  for v1? (Lean: presence for v1, equality cross-check as a follow-up.)
- Final CLI name: `eqa verify-templates` vs. a `--templates` mode on
  `eqa validate`. (Lean: dedicated subcommand for a clean exit-code gate.)
