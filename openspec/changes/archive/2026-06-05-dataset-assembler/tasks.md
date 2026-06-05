## 1. Make rendering always-on

- [x] 1.1 In `questions/cli_handler.py`, remove the `if getattr(args, "render", False)`
  guard — render schematic unconditionally after question generation.
- [x] 1.2 In `cli.py`, mark `--render` on questions as a deprecated no-op (keep
  for backwards compat).

## 2. Dataset assembler

- [x] 2.1 Add `src/electronics_qa_generator/output/assembler.py` with
  `assemble_dataset(items, schematic_paths, topology, seed, out_dir)`: writes JSONL
  lines with MMMU schema (id, question, answer, options, explanation, image); copies
  PNGs to `images/` subdirectory.
- [x] 2.2 Map item types: direct → `answer` string; classification → `options` as
  JSON-encoded list + `answer` as label; comparison → `answer` as boolean label.

## 3. Assemble CLI subcommand

- [x] 3.1 Add `eqa assemble` to `cli.py` with `--out` (default `dataset/`), `--seed`,
  `--cache-dir`, `--no-cache`.
- [x] 3.2 Add `src/electronics_qa_generator/output/assemble_cli.py`:
  `run_assemble(args)` — loops over all 5 topologies, runs full pipeline per
  topology, collects items + schematic paths, calls `assemble_dataset()`, runs
  validation, writes `report.json`.

## 4. Tests

- [x] 4.1 Add `tests/test_output/test_assembler.py`: test JSONL output format for
  each question type; test id generation; test image path relativity.
- [x] 4.2 Add CLI tests: `eqa assemble --out tmpdir` produces expected files.
- [x] 4.3 Update existing emit tests if rendering is always-on.

## 5. Validation

- [x] 5.1 Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`; all
  must pass.
