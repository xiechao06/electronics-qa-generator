## Why

Batch generation produces 22,232 schematic PNGs dumped into a single flat `images/` directory, making it impossible to browse or manage per-topology. With 14 topologies each generating 1,588 images, and more to come, a flat structure is unsustainable for human inspection and tooling. Organizing images by topology simplifies the directory structure, aligns with the existing per-topology output pattern already used for netlists and JSON records, and makes it trivial to find all schematics for a given circuit family.

## What Changes

- **Image output directories**: All schematic renderers (emit, questions, batch generation, assembler) write images into topology-named subdirectories under `images/` instead of a flat `images/` directory.
- **Schematic path references**: The `schematic_path` field in QA items changes from `images/voltage_divider_0000002a.png` to `images/voltage_divider/0000002a.png`, reflecting the new directory structure.
- **Batch script update**: `scripts/batch_generate.py` updated to use the new path convention.
- **Assembler update**: The dataset assembler's image copying logic updated to handle per-topology subdirectories.

Existing image files and data are not migrated — regeneration uses the new structure automatically.

## Capabilities

### New Capabilities
- `per-topology-image-folders`: Schematic PNGs are organized into `images/<topology>/` subdirectories instead of a single flat directory.

### Modified Capabilities
- `svg-schematic-renderer`: The rendered schematic output path changes to include a topology subdirectory.

## Impact

- `src/electronics_qa_generator/questions/cli_handler.py` — `schematic_path` construction
- `src/electronics_qa_generator/output/emit.py` — emit schematic path
- `src/electronics_qa_generator/output/assembler.py` — image copy logic
- `src/electronics_qa_generator/output/assemble_cli.py` — schematic path reference
- `scripts/batch_generate.py` — worker image path construction
- `src/electronics_qa_generator/render/schematic.py` — only if it constructs paths internally
- All `schematic_path` references in QA item JSONL output change format
