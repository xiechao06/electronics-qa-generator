## 1. Record serialization

- [x] 1.1 Create `output/serialize.py` with `record_to_dict(record)` flattening `CircuitRecord` and nested `SimulationConfig` (None → null)
- [x] 1.2 Add `record_to_json(record, *, indent=2)` returning valid JSON parseable back to `record_to_dict` output
- [x] 1.3 Export `record_to_dict` and `record_to_json` from `output/__init__.py`

## 2. Template lookup

- [x] 2.1 Add a `get_template(name)` helper and a `topology -> template` mapping built from `ALL_TEMPLATES` (in `output/emit.py`)

## 3. Emit command

- [x] 3.1 Create `output/emit.py` with `run_emit(args)` handling `--list`, single topology, `--all`, `--seed`, and `-o/--out`
- [x] 3.2 Implement stdout mode: print netlist, delimiter line, then JSON record
- [x] 3.3 Implement file mode: write `<topology>_<seed>.cir` and `.json` to the output dir, creating it if missing
- [x] 3.4 Implement `--list` (print topologies, exit 0) and unknown-topology error (list valid names, non-zero exit)

## 4. CLI wiring

- [x] 4.1 Add an `emit` subparser to `build_parser()` in `cli.py` with positional topology, `--list`, `--all`, `--seed`, `-o/--out`
- [x] 4.2 Dispatch `emit` to `run_emit` in `main()`; leave `generate` behavior unchanged

## 5. Tests

- [x] 5.1 Write `tests/test_output/test_serialize.py`: dict has all fields, simulation flattened, None → null, JSON round-trips via `json.loads`, deterministic output
- [x] 5.2 Write `tests/test_output/test_emit.py`: `--list` prints all topologies; single emit prints netlist + JSON; unknown topology errors non-zero
- [x] 5.3 Add file-mode tests (use `tmp_path`): single and `--all` write `.cir`+`.json` pairs; output dir auto-created; same seed → byte-identical files

## 6. Verification

- [x] 6.1 Run `uv run pytest -v` — all tests pass (55 passed)
- [x] 6.2 Run `uv run ruff check .` and `uv run ruff format --check .` — clean
- [x] 6.3 Manual smoke: `uv run eqa emit --list`, `uv run eqa emit rc_lowpass --seed 42`, `uv run eqa emit --all -o /tmp/eqa_emit`
