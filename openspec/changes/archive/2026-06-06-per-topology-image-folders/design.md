## Context

The batch generation pipeline currently writes all 22,232 schematic PNGs into a single flat `images/` directory. With 14 topologies and growing, this is unmanageable — there's no way to quickly locate all schematics for a given topology, count them, or visually inspect one family.

The per-topology directory pattern already exists for other artifacts: `output/<topology>/` holds netlists (`.cir`) and JSON records (`.json`). Images are the only output type that breaks this convention.

Four code paths construct `schematic_path` values:
1. `eqa questions` CLI handler
2. `eqa emit` CLI handler
3. Dataset assembler (`output/assembler.py`, `output/assemble_cli.py`)
4. Batch generation script (`scripts/batch_generate.py`)

All four construct paths in the form `images/{topology}_{seed_hex}.png`. The change is mechanical: add a topology subdirectory.

## Goals / Non-Goals

**Goals:**
- All schematic PNGs written to `images/<topology>/<seed_hex>.png`
- `schematic_path` field in QA items reflects the new structure
- All three CLI subcommands (`emit`, `questions`, `assemble`) and the batch script use the new convention
- Backward compatibility: nothing breaks for callers of the render API (which takes an explicit output path)

**Non-Goals:**
- Migrating existing images or data
- Changing the seed-hex naming scheme
- Adding any new CLI flags or configuration
- Modifying the `render_schematic()` public API signature

## Decisions

### Decision 1: Subdirectory by topology name, not family

The topology name (`voltage_divider`, `rc_lowpass`, etc.) is used as the subdirectory because it's already the canonical identifier everywhere (template registry, CLI, fact extractors). Using family (`passive`, `transistor`, `opamp`) would require a lookup and doesn't add value since topology names are already unique.

### Decision 2: Each site creates its own directory

Each code path that writes an image calls `mkdir(parents=True, exist_ok=True)` on the target directory. This avoids a centralized "ensure all directories exist" step and keeps each call site self-contained. The overhead of `mkdir` on an existing directory is negligible.

**Alternative considered:** A centralized `get_image_path(topology, seed)` utility function. Rejected because the 4 call sites have slightly different needs (some use seed hex, some use `record.id`, the assembler copies existing files). A single function would need flags to handle all cases, adding indirection without reducing complexity.

### Decision 3: Remove topology prefix from filename

Files change from `images/voltage_divider_0000002a.png` to `images/voltage_divider/0000002a.png`. The topology name was redundant in the filename since it's now the directory. The assembler's copy logic already renames files with a topology prefix; this is kept to avoid collisions when copying into a flat target, but the source structure drops the prefix.

**Alternative considered:** Keep `images/voltage_divider/voltage_divider_0000002a.png`. Rejected because it's redundant and makes filenames longer with no benefit.

## Risks / Trade-offs

- **[Low] Existing QA item JSONL files have old paths** → Not migrating; regeneration uses the new structure automatically. The old `output/batch/` directory is ephemeral.
- **[Low] Assembler may reference old paths** → The assembler constructs paths from topology+seed, not from stored `schematic_path`. Confirmed by code review.
