## Context

The pipeline produces 25 QA items across 5 topologies but in an internal format with
extra metadata fields (program, answer_value, tolerance, verified). The MMMU benchmark
expects a simpler schema: id, question, options, answer, explanation, image. The
Assembler stage bridges this gap.

## Goals / Non-Goals

**Goals:**
- Transform QA items into MMMU JSONL with proper id scheme and image paths.
- Bundle schematics into a self-contained output directory.
- Make schematic rendering always-on for `eqa questions`.

**Non-Goals:**
- Train/val/test splitting (future work).
- Parquet output (JSONL only for MVP).
- Base64-embedded images (relative paths for now).

## Decisions

### Decision: Always render schematics in questions
Remove the conditional `--render` check in `cli_handler.py`. Rendering is now
unconditional. `--render` flag stays in `cli.py` as a no-op to avoid breaking
existing scripts.
- **Why:** A multimodal benchmark needs images; making rendering opt-in adds
  friction with no benefit.

### Decision: MMMU-compatible id scheme
`id = f"{topology}_{seed & 0xFFFFFFFF:08x}_{item_index}"`. Example:
`rc_lowpass_0000002a_0`. Unique, reproducible, human-readable.
- **Why:** Matches MMMU's `validation_Electronics_N` pattern; seed ensures
  reproducibility.

### Decision: Assembly in `output/assembler.py`
A single function `assemble_dataset(items, schematic_paths, output_dir)` writes the
JSONL and copies images. No new class — just a function.
- **Why:** Simple, testable, fits the existing output subpackage.

## Risks / Trade-offs

- **Always rendering slows down questions** → matplotlib rendering is ~0.1s per
  topology; negligible vs. Xyce simulation.
- **Image paths are relative** → The dataset directory must not be moved without
  also moving the `images/` subdirectory.

## Migration Plan

1. Add `output/assembler.py`.
2. Make rendering unconditional in `questions/cli_handler.py`.
3. Add `eqa assemble` subcommand.
4. Add tests.
- **Rollback:** Remove the `assemble` subcommand.

## Open Questions

- Should `eqa assemble` also run `eqa validate` and include the report? Yes.
