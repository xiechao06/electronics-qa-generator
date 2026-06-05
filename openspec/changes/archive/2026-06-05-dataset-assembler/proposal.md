## Why

The pipeline generates 25 QA items with ground-truth answers, schematics, explanations,
and verification — but they remain in an internal format. To produce an MMMU-compatible
benchmark dataset, we need an Assembler stage that transforms internal `QAItem` objects
into JSONL files with the full MMMU schema (id, question, options, answer, explanation,
image path) and bundles all artifacts into a self-contained output directory.

Additionally, schematic images should always be generated alongside questions — the
`--render` flag adds unnecessary friction for a multimodal benchmark.

## What Changes

- Make schematic rendering **always on** for `eqa questions` — remove `--render` flag;
  images are produced automatically. Keep `--render` on `eqa emit` unchanged.
- Add `output/assembler.py`: a Dataset Assembler that converts a list of `QAItem`
  objects into MMMU-compatible JSONL, mapping internal fields to the target schema:
  - `id` → topology + seed + item index
  - `question` + `<image N>` reference
  - `options` → JSON-encoded choices list (for classification/MC items)
  - `answer` → answer string (open-ended) or answer index (MC)
  - `explanation` → LLM-generated or null
  - `schematic_path` → relative path to rendered PNG
- Add `eqa assemble` subcommand: runs the full pipeline for all 5 topologies, generates
  25 items with schematics, assembles JSONL, and writes everything to an output dir.
- Output structure:
  ```
  out/
    dataset.jsonl       # all QA items
    images/
      voltage_divider_0000002a.png
      rc_lowpass_0000002a.png
      ...
    report.json         # validation summary
  ```
- Mark the `--render` flag on `eqa questions` as deprecated (still accepted, no-op
  since rendering is always on).

## Capabilities

### New Capabilities
- `dataset-assembler`: Transform internal QA items into MMMU-compatible JSONL with
  proper id, options, image references, and answer format. Bundle schematics into a
  self-contained output directory.
- `assemble-cli`: `eqa assemble` subcommand running the full pipeline across all
  topologies and producing a complete dataset.

### Modified Capabilities
- `render-always-on`: Schematic rendering is always performed during `eqa questions`
  — the `--render` flag is deprecated and a no-op.

## Impact

- **Code**: `output/assembler.py` (new); `questions/cli_handler.py` (render always
  on); `cli.py` (+ `assemble` subcommand, deprecation note on `--render`).
- **Dependencies**: None new.
- **Invariant**: Assembler never alters answers; it only reformats and bundles.
