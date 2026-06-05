## 1. Check result model

- [x] 1.1 Add `src/electronics_qa_generator/validation/__init__.py` and
  `src/electronics_qa_generator/validation/models.py` with `Verdict` enum
  (PASS, FAIL, WARN) and `CheckResult` dataclass (name, verdict, message).

## 2. Static check functions

- [x] 2.1 Add `src/electronics_qa_generator/validation/checks.py` with function
  signatures: `check_answer(item, facts)`, `check_params(item, params)`,
  `check_unit(item)`, `check_leakage(item)`, `check_degenerate(item)`,
  `check_tolerance(item)`, `check_coverage(items_per_topology)`.
- [x] 2.2 Implement `check_answer`: rerun `compute_answer` from facts via the stored
  program; assert answer, answer_value, unit, tolerance match byte-for-byte.
- [x] 2.3 Implement `check_params`: for each key in `params` (e.g., `R1_ohm`),
  format the value with its unit prefix, then substring-search the question text for
  that formatted value. PASS if all found; FAIL on any missing.
- [x] 2.4 Implement `check_unit`: extract the expected unit from the `format_numeric`
  step in the program; search the question text for a conflicting unit mention
  (e.g., "Provide answer in kHz" vs. answer unit "Hz"). PASS if consistent.
- [x] 2.5 Implement `check_leakage`: regex-extract the numeric answer value or answer
  string; search the question text. If found and the answer is non-trivial (>2 chars,
  not a classification label), return WARN.
- [x] 2.6 Implement `check_degenerate`: if `answer_value` is None, NaN, ±inf, or
  exceeds a unit-dependent threshold (freq 0.0 or >1e9, voltage <−1e3 or >1e6, gain
  <−200 dB), return FAIL.
- [x] 2.7 Implement `check_tolerance`: if `answer_value` is non-zero and magnitude >
  1e-6, compute relative tolerance = tolerance / |answer_value|; FAIL if rel > 0.5.
  For near-zero values, use absolute tolerance floor.
- [x] 2.8 Implement `check_coverage`: for a list of QA items from one topology, ensure
  at least 2 distinct `question_type` values are present and no two items sharing an
  `id` have identical question text; WARN if type diversity < 2, FAIL if duplicates.

## 3. Validation report

- [x] 3.1 Add `src/electronics_qa_generator/validation/report.py` with
  `ValidationReport` dataclass: `items: list[list[CheckResult]]`, `ok: bool`,
  `to_json()` method, and aggregate properties (`total_checks`, `fail_count`,
  `pass_count`, `warn_count`).

## 4. CLI integration

- [x] 4.1 Add `eqa validate` subcommand to `cli.py`: topology, seed, --list, --json
  args; calls `run_validate` from the handler.
- [x] 4.2 Add `src/electronics_qa_generator/validation/cli_handler.py` with
  `run_validate(args)`: full pipeline → generate items → run all checks → build
  report → print (text or JSON) → exit 0 or 1.
- [x] 4.3 Add `--verify` flag to `eqa questions` in `cli.py`; in
  `questions/cli_handler.py`, when set, run checks and include `verified` and
  `verification_errors` in each item's output dict.

## 5. Tests

- [x] 5.1 Add `tests/test_validation/test_checks.py`: ~15 tests covering each check's
  pass, fail, and edge cases (NaN, negative tolerance, missing params, unit mismatch,
  leaked answer, degenerate value).
- [x] 5.2 Add `tests/test_validation/test_report.py`: test report aggregation,
  serialization, `ok` flag.
- [x] 5.3 Add `tests/test_validation/test_cli.py`: test `eqa validate` output, exit
  codes, and `eqa questions --verify` embedding.

## 6. Docs and validation

- [x] 6.1 Document `eqa validate` and `--verify` in `README.md`.
- [x] 6.2 Run `uv run pytest`, `uv run ruff check .`, and `uv run ruff format .`; all
  must pass.
