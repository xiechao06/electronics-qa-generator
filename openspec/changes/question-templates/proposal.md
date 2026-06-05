## Why

Five templates generate circuits and extraction computes facts — but the pipeline stops there. To produce a benchmark dataset we need the question engine: the stage that turns a fact table into CLEVR-style Q/A items. Every question must have a deterministic answer computed from facts (never from an LLM), a machine-readable program showing how the answer was derived, and a classification by type (direct, derived, classification, comparison). This bridges the gap between fact extraction and the downstream LLM paraphrase/rendering stages.

## What Changes

- A **question template system**: each circuit topology defines 2–4 question templates, each specifying a question type, a text template with `{param}` slots, an answer computation function, and a CLEVR-style program.
- A **program representation**: each question carries a `program` list of `{"op": "...", "args": [...]}` dicts that mirrors CLEVR's functional program format. Programs are written once per template, computed deterministically per sample.
- **Answer computation**: pure functions that take the `fact_dict` and `parameter_dict` and return an `(answer_value, answer_text, unit, tolerance)` tuple. No LLM involvement.
- **Question type taxonomy**: `direct` (read a fact), `derived` (compute from facts), `classification` (pick a label), and `comparison` (relative to a reference).
- At least **2 QA items per circuit template** (10+ total), each producing a `QAItem` record.
- A **`QUESTION_TEMPLATES` registry** mapping topology name → list of question spec dicts, symmetric to `FACT_EXTRACTORS`.
- Wire into `eqa questions` subcommand: given a topology and seed, simulate (or use cache), extract facts, generate all questions, print JSON array of `QAItem` records.

## Capabilities

### New Capabilities
- `question-templates`: Per-topology question template definitions, CLEVR-style program generation, deterministic answer computation, `QUESTION_TEMPLATES` registry, and `generate_questions(topology, facts, params) -> list[QAItem]`.
- `question-cli`: The `eqa questions` subcommand — given a topology and seed, run the full pipeline (sample → simulate → extract → generate questions) and print QA items as JSON.

### Modified Capabilities
<!-- None -->

## Impact

- **New:** `src/electronics_qa_generator/questions/` package with `__init__.py`, `templates.py` (question specs + registry), `programs.py` (CLEVR-style program builders), `generator.py` (question generation engine)
- **Modified:** `cli.py` — new `eqa questions` subparser
- **Dependencies:** stdlib only. Uses existing `SimulationConfig`, `QAItem`, `CircuitRecord` from `models.py`. Calls into `simulation/`, `extraction/`, and `templates/` to run the full pipeline.
- **Tests:** `tests/test_questions/` — template count, program correctness, answer accuracy, registry integrity, CLI smoke
