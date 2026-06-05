## 1. Question templates data

- [x] 1.1 Create `questions/templates.py` with `QUESTION_TEMPLATES` registry — 2–4 question templates per of the 5 topologies (16 total)
- [x] 1.2 Define the template dict schema: `id`, `question_type`, `question_template`, `program`, `answer_keys`, `answer_formatter`
- [x] 1.3 Implement question templates for `voltage_divider`: direct Vout_dc, derived divider_ratio, comparison Vout vs Vin/2
- [x] 1.4 Implement question templates for `rc_lowpass`: direct cutoff_hz, classification behavior, comparison cutoff vs 1kHz
- [x] 1.5 Implement question templates for `rc_highpass`: direct cutoff_hz, classification behavior, comparison cutoff vs 1kHz
- [x] 1.6 Implement question templates for `rlc_bandpass`: direct center_freq_hz, derived Q, classification behavior, comparison bandwidth vs threshold
- [x] 1.7 Implement question templates for `half_wave_rectifier`: direct Vout_dc, derived ripple ratio (ripple_vpp / Vout_dc), comparison ripple vs threshold

## 2. CLEVR-style programs

- [x] 2.1 Create `questions/programs.py` with op definitions: `READ_FACT`, `READ_PARAM`, `ADD`, `SUB`, `MUL`, `DIV`, `ABS`, `COMPARE`, `CLASSIFY`, `FORMAT_NUMERIC`, `RETURN_BOOL`, `RETURN_LABEL`
- [x] 2.2 Define program builder helpers: `program_read_fact(key)`, `program_classify(key, labels)`, `program_compare(key, op, ref)`, etc.

## 3. Answer computation engine

- [x] 3.1 Create `questions/compute.py` with `compute_answer(program, facts, params) -> (answer_value, answer_text, unit, tolerance)`
- [x] 3.2 Implement the program interpreter: walk ops, maintain a result stack, evaluate each op
- [x] 3.3 Unit map: define default units for each fact key (V, Hz, dB, ratio, etc.)
- [x] 3.4 Tolerance derivation from format_numeric precision

## 4. Question generator

- [x] 4.1 Create `questions/generator.py` with `generate_questions(topology, facts, params) -> list[QAItem]`
- [x] 4.2 Populate QAItem fields: question_type, question (formatted text), answer (text), answer_value, unit, tolerance, choices, program, explanation (None for now)

## 5. Package exports

- [x] 5.1 Create `questions/__init__.py` with exports: `QUESTION_TEMPLATES`, `compute_answer`, `generate_questions`

## 6. CLI wiring

- [x] 6.1 Create `questions/cli_handler.py` with `run_questions(args)` handling pipeline: simulate → extract → generate → print
- [x] 6.2 Add `eqa questions` subparser to `cli.py` with `--seed`, `--list`, `--cache-dir`, `--no-cache`, `--jsonl`
- [x] 6.3 Dispatch `questions` command to `run_questions` in `main()`

## 7. Tests

- [x] 7.1 Write `tests/test_questions/test_templates.py` — registry has 5 topologies, 2+ templates each, correct types
- [x] 7.2 Write `tests/test_questions/test_programs.py` — program builder helpers produce correct structures
- [x] 7.3 Write `tests/test_questions/test_compute.py` — direct/derived/classification/comparison answer computation
- [x] 7.4 Write `tests/test_questions/test_generator.py` — QAItem fields populated, error on unknown topology

## 8. Verification

- [x] 8.1 Run `uv run pytest -v` — all tests pass
- [x] 8.2 Run `uv run ruff check .` and `uv run ruff format --check .` — clean
- [x] 8.3 Manual smoke: `uv run eqa questions --list`, `uv run eqa questions rc_lowpass --seed 42 --no-cache` (requires Xyce)
