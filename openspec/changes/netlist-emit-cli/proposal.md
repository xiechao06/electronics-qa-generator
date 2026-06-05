## Why

The five circuit templates from `setup-circuit-families` can produce `CircuitRecord` objects in Python, but there is no way to drive them from the command line or persist their output. To inspect netlists, hand them to Xyce, or build the simulation stage, we need a small utility that turns a named template + seed into a Xyce netlist file plus a machine-readable JSON record. This is the bridge between the template library and the rest of the pipeline (simulation, dataset assembly), and it makes templates testable by humans today.

## What Changes

- Add a **`CircuitRecord` → JSON serializer** that converts a record (including its nested `SimulationConfig`) into a stable, machine-readable dict/string. This is reusable by the future dataset assembler, not just the CLI.
- Add a new **`eqa emit` subcommand** that:
  - lists available templates (`eqa emit --list`)
  - samples a named template with an optional `--seed` for reproducibility
  - writes the **Xyce netlist** (`.cir`) and the **JSON record** (`.json`) either to stdout or to an output directory
  - supports emitting all templates at once (`eqa emit --all`)
- Wire the subcommand into the existing `cli.py` argument parser alongside `generate`.
- The JSON record schema mirrors the `CircuitRecord` fields (`id`, `family`, `topology`, `difficulty`, `parameters`, `netlist`, `simulation`, `probes`) so downstream stages can consume it directly.

## Capabilities

### New Capabilities
- `circuit-record-serialization`: Deterministic conversion of `CircuitRecord` (and its nested `SimulationConfig`) to a JSON-compatible dict and string. Round-trippable field names, stable key ordering, numeric values preserved.
- `netlist-emit-cli`: The `eqa emit` subcommand — list templates, sample one (or all) by name with a seed, and write netlist + JSON record to stdout or files.

### Modified Capabilities
<!-- None — `eqa generate` is untouched; `emit` is a new sibling subcommand. -->

## Impact

- **Package:** new `src/electronics_qa_generator/output/serialize.py` (record → JSON); new `src/electronics_qa_generator/cli_emit.py` (or extend `cli.py`) for the subcommand
- **CLI:** `cli.py` gains an `emit` subparser; `eqa generate` behavior unchanged
- **Models:** no changes to `models.py` dataclasses (serializer reads them as-is)
- **Dependencies:** none beyond stdlib (`json`, `argparse`, `pathlib`)
- **Tests:** new tests for the serializer and the `emit` command (list, single, all, file output, determinism)
