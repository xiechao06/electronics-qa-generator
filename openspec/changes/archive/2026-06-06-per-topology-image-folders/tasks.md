## 1. CLI handlers — `schematic_path` construction

- [x] 1.1 Update `src/electronics_qa_generator/questions/cli_handler.py` to write images to `images/<topology>/<seed_hex>.png` and set `schematic_path` accordingly
- [x] 1.2 Update `src/electronics_qa_generator/output/emit.py` to write schematics to `images/<topology>/<seed_hex>.png` and set `schematic_path` accordingly

## 2. Dataset assembler

- [x] 2.1 Update `src/electronics_qa_generator/output/assembler.py` to handle per-topology image subdirectories when copying images into the assembled dataset
- [x] 2.2 Update `src/electronics_qa_generator/output/assemble_cli.py` if it constructs `schematic_path` references directly

## 3. Batch generation script

- [x] 3.1 Update `scripts/batch_generate.py` worker to write images to `images/<topology>/<seed_hex>.png` and include the per-topology path in each QA item

## 4. Verification

- [x] 4.1 Run `uv run pytest` — confirm all existing render and template tests pass
- [x] 4.2 Run a small batch (`--total 200`) and verify images land in `images/<topology>/` subdirectories
- [x] 4.3 Verify QA item `schematic_path` values use the new `images/<topology>/<seed>.png` format
- [x] 4.4 Verify `eqa emit --render` and `eqa questions` both produce per-topology image paths

## 5. Cleanup

- [x] 5.1 Run `uv run ruff check .` on all modified files
