## Context

The `setup-circuit-families` change delivered five templates (`VoltageDivider`, `RCLowPass`, `RCHighPass`, `RLCBandPass`, `HalfWaveRectifier`) exposed via `ALL_TEMPLATES`, each returning a `CircuitRecord`. The CLI (`cli.py`) currently has only a placeholder `generate` subcommand. The `output/` package is a stub. We need a way to run a template and persist its netlist + structured record from the command line. Python 3.14, stdlib only.

## Goals / Non-Goals

**Goals:**
- A pure-function serializer `record_to_dict` / `record_to_json` that turns a `CircuitRecord` into a JSON-compatible structure with stable key order.
- An `eqa emit` subcommand that lists templates, samples one or all by name with a seed, and writes a `.cir` netlist + `.json` record to stdout or an output directory.
- Reproducible output (seed-driven), human-inspectable, and consumable by the future simulation stage.

**Non-Goals:**
- Running Xyce or validating the netlist electrically — that's the `simulation/` stage.
- Serializing `QAItem` / `Sample` (only `CircuitRecord` + `SimulationConfig` are in scope now).
- A general dataset export format (Parquet/JSONL bundles) — that's the dataset assembler.
- Round-trip deserialization (JSON → `CircuitRecord`); only forward serialization is required now.

## Decisions

### 1. Serializer lives in `output/serialize.py` as plain functions

Use module-level functions, not methods on the dataclasses, to keep `models.py` dependency-free and presentation-agnostic.

```python
def record_to_dict(record: CircuitRecord) -> dict[str, Any]: ...
def record_to_json(record: CircuitRecord, *, indent: int = 2) -> str: ...
```

`record_to_dict` flattens `SimulationConfig` into a nested dict:

```json
{
  "id": "rc_lowpass_0000002a",
  "family": "passive",
  "topology": "rc_lowpass",
  "difficulty": 1,
  "parameters": {"R1_ohm": 18000.0, "C1_f": 4.7e-09},
  "netlist": "* RC low-pass filter\n...",
  "simulation": {"type": "ac", "tool": "Xyce", "params": {"start_hz": 0.01, ...}},
  "probes": ["V(out)"]
}
```

`None` simulation serializes as `null`. Key order follows the dataclass field order for stability.

**Alternative considered:** `dataclasses.asdict`. Rejected as the sole mechanism — it works but gives no control over key order, `None` handling, or future field filtering. We wrap it in an explicit function so the JSON schema is owned by the serializer, not incidental to the dataclass.

### 2. `emit` subcommand structure

Add an `emit` subparser to `build_parser()` in `cli.py`. Keep the handler logic in a separate module (`output/emit.py`) so `cli.py` stays a thin dispatcher.

Flags:

| Flag | Meaning |
|---|---|
| `--list` | Print available template topologies and exit |
| `<topology>` (positional, optional) | Which template to emit (e.g., `rc_lowpass`) |
| `--all` | Emit every template in `ALL_TEMPLATES` |
| `--seed N` | Seed for reproducible sampling (default: 0) |
| `-o, --out DIR` | Write files to DIR instead of stdout |

Behavior:
- `eqa emit --list` → one topology per line, exit 0.
- `eqa emit rc_lowpass` → print netlist, then a separator, then JSON to stdout.
- `eqa emit rc_lowpass -o build/` → write `build/rc_lowpass_<seed>.cir` and `build/rc_lowpass_<seed>.json`.
- `eqa emit --all -o build/` → write a pair of files per template.
- Unknown topology → error message listing valid names, exit code 2.

### 3. Template lookup by topology name

Build a `dict[str, CircuitTemplate]` from `ALL_TEMPLATES` keyed by `template.topology`. This is the canonical name users pass on the command line. A helper `get_template(name)` returns the instance or raises a `KeyError`-derived CLI error.

### 4. File naming and output layout

Files are named `<topology>_<seed:08x>.cir` and `.json`, matching the `CircuitRecord.id` convention from the templates. The `.cir` extension is the conventional SPICE/Xyce netlist extension. Output directory is created if missing (`mkdir(parents=True, exist_ok=True)`).

### 5. Stdout format when no `-o`

When writing to stdout, print the netlist first, then a clear delimiter line (`# --- record.json ---`), then the JSON. This keeps a single command's output copy-pasteable and greppable, while `-o` produces clean separate files for tooling.

## Risks / Trade-offs

- **[Risk] Stdout mixing netlist + JSON could confuse downstream piping** → **Mitigation**: the `-o DIR` mode produces clean, separate files for any programmatic use; stdout mode is for human inspection only.
- **[Risk] Seed default of 0 makes repeated calls identical** → Intended for reproducibility; users vary `--seed` to get different instances. Documented in `--help`.
- **[Trade-off] Forward-only serialization** (no JSON → record) → Acceptable; nothing needs to reconstruct a `CircuitRecord` from JSON yet. Field names are kept explicit so a loader is trivial to add later.
- **[Risk] `float` formatting in JSON** (e.g., `4.7e-09`) → Standard `json.dumps` output is valid and parseable; we accept Python's default float repr.

## Open Questions

- Should `--all` to stdout be allowed, or only to `-o`? Initial decision: allow stdout for `--all` but separate records with the delimiter and a per-template header comment, so it stays inspectable.
- Netlist file extension `.cir` vs `.sp` vs `.net` — chose `.cir` (common Xyce convention); revisit if the simulation stage prefers another.
