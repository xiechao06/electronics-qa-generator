## Why

The pipeline produces QA items but has no quality gate — bugs like zero-value answers
and answer leakage went undetected until manual review. We need a **Verifier** stage
(architecture §11) that runs deterministic static checks on every generated QA item
before it enters the dataset. These checks catch regressions, enforce invariants, and
act as a CI gate — all without requiring an LLM.

## What Changes

- Add a `validation/` subpackage with static correctness checking functions.
- Implement 7 static checks (the "no LLM needed" tier from the Verifier backlog):
  1. **Answer recomputation** — rerun the CLEVR program from stored facts and assert
     answer matches byte-for-byte.
  2. **Parameter consistency** — verify R/C/L values in question text match
     `circuit.parameters`.
  3. **Unit consistency** — detect unit mismatches between question text and answer.
  4. **Literal answer leakage** — regex-detect answer string or value in question text.
  5. **Degenerate value detection** — flag NaN, ±inf, or physically impossible values.
  6. **Tolerance appropriateness** — reject relative tolerances >50% of magnitude.
  7. **Template coverage** — assert type diversity and seed variation per topology.
- Add a `ValidationReport` model collecting per-item and aggregate results.
- Wire the verifier as an opt-in `--verify` flag on `eqa questions` and expose a
  standalone `eqa validate` command.
- All checks are pure functions of `QAItem` + `facts` + `params` → no I/O, no LLM.

## Capabilities

### New Capabilities
- `static-verifier`: The 7 deterministic QA-item quality checks covering answer
  correctness, parameter consistency, unit matching, leakage detection, degenerate
  values, tolerance bounds, and template coverage.
- `validation-report`: A structured `ValidationReport` model with per-item verdicts
  (pass/fail/warn) and aggregate statistics.
- `validate-cli`: A new `eqa validate` subcommand and opt-in `--verify` flag on
  `eqa questions` that runs the static verifier and reports results.

### Modified Capabilities
<!-- None -->

## Impact

- **Code**: `src/electronics_qa_generator/validation/` (new subpackage: `checks.py`,
  `report.py`, `cli_handler.py`); `cli.py` (+ `validate` subcommand, + `--verify`
  on `questions`).
- **Dependencies**: None — all checks are pure Python (regex, math, property access).
- **Invariant**: Verifier runs *after* QA generation, never before. It observes
  results but never modifies them.
- **Tests**: ~20 new tests covering each check's pass, fail, and edge cases.
