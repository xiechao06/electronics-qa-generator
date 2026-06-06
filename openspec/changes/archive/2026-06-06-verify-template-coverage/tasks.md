# Implementation Tasks

## 1. Netlist fact model

- [x] 1.1 Add `validation/template_coverage.py` with a `NetlistFact` dataclass
  (kind: `component | node | model | analysis`, designator/name, value/params)
  and a `CoverageReport`/`TopologyReport` result type (per-topology status +
  list of failures with kind + locus).
- [x] 1.2 Implement `netlist_facts(graph: CircuitGraph) -> list[NetlistFact]`
  that derives one fact per component (designator + params/value), per non-ground
  node, per device model name, and one for the analysis directive — deterministic,
  no simulation.
- [x] 1.3 Unit-test `netlist_facts` for a passive topology and a transistor
  topology (asserts every component designator, every non-ground node, model
  names, and the analysis directive appear).

## 2. Netlist → image coverage

- [x] 2.1 Implement `image_covered_facts(graph, template) -> set[str]` that
  renders via `fill_template` and detects which component designators and
  non-ground nodes are present in the rendered SVG (slot ids + word-boundary
  label text; avoid `R1`/`R12` substring false-positives).
- [x] 2.2 Implement the image-coverage check: report a FAIL for every component or
  node in `netlist_facts` not present in the rendered SVG.
- [x] 2.3 Tests: passes for all current topologies; fails with a clear locus when
  a component is removed from a template fixture.

## 3. Question → fact dependency mapping

- [x] 3.1 Define an explicit per-topology fact→inputs dependency table (kept
  beside `questions/templates.py`) mapping derived facts (e.g. `Vout_dc`,
  `cutoff_hz`) to the governing component/param inputs a solver must read.
- [x] 3.2 Implement `question_answer_inputs(template_entry) -> set[str]` deriving
  answer-relevant facts from `answer_keys` + the program's `read_fact`/
  `read_param` ops, expanded through the dependency table.
- [x] 3.3 Implement `question_covered_facts(question_template, params) -> set[str]`
  detecting facts conveyed by inlined `{param}` placeholders in the question text.

## 4. Triad coverage check + report

- [x] 4.1 Implement `verify_topology(family, topology, registry) -> TopologyReport`
  that combines image-covered ∪ question-covered facts and reports a FAIL for any
  answer-relevant fact visible in neither (with topology, question id, fact).
- [x] 4.2 Implement `verify_all(registry) -> CoverageReport` iterating every
  registered topology (sampling a fixed seed) and aggregating PASS/FAIL.
- [x] 4.3 Implement report rendering: human-readable text and JSON
  (`to_json()`), each FAIL identifying the specific missing component, node, or
  hidden answer-relevant fact.

## 5. Strengthen registry validation (bidirectional)

- [x] 5.1 Extend `TemplateRegistry._validate` so every graph component and every
  non-ground node must be represented in the template (slot or visible label),
  in addition to the existing "declared slots ⊆ components/nodes" check.
- [x] 5.2 Raise `ValueError` naming the missing designator/node; ensure no PNG is
  produced from an incomplete template.
- [x] 5.3 Tests: bidirectional validation rejects a graph with an undrawn
  component and an undrawn node; all current topologies still resolve.

## 6. CLI surface

- [x] 6.1 Add an `eqa verify-templates` subcommand (wired in `cli.py` + a
  validation `cli_handler`) that runs `verify_all()` and prints the report.
- [x] 6.2 Support `--json` output and exit non-zero when any topology FAILs so it
  can gate batch generation.
- [x] 6.3 Test the CLI: exit 0 when all pass; exit non-zero + locus in output when
  a topology fails.

## 7. Regression + docs

- [x] 7.1 Add an all-topologies regression test invoking `verify_all()` that fails
  on any coverage failure (generalizing the existing schematic-completeness test;
  fold that test into the new module).
- [x] 7.2 Document the verifier in `AGENTS.md` (pre-flight before batch
  generation) and `README.md` (pipeline/commands).
- [x] 7.3 Run `uv run pytest` (ignoring the known unrelated `test_llm` dotenv
  failure) and `uv run ruff check .` / `ruff format .`; confirm green.
