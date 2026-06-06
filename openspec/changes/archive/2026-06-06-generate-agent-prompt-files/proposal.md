## Why

Currently the batch pipeline produces `qa_items.jsonl` and per-topology schematic
images, but there is no easy way to feed the generated Q/A pairs to an external
agent (Perplexity, ChatGPT, Claude) for verification. The user must manually
match images to questions, copy-paste text, and track which questions have been
answered — a tedious, error-prone process that discourages routine verification.

## What Changes

- During batch generation, emit **prompt markdown files** alongside schematics.
  Each prompt file references one schematic image and lists all questions for
  that image in a numbered format an external agent can ingest directly.
- Emit a parallel **answer markdown file** per prompt containing the
  ground-truth answers (extracted from the QA items), so the user can compare
  agent responses against known truths without peeking at the netlist.
- Organise these files in a clean `output/batch/prompts/` directory tree,
  mirroring the `images/` layout.
- Integrate prompt/answer-file generation as a post-processing step within
  `scripts/batch_generate.py`, behind a flag so existing workflows are
  unchanged.

## Capabilities

### New Capabilities
- `agent-prompt-generation`: Emit per-schematic prompt and answer markdown files
  during batch generation, formatted for external VLM/agent verification.

### Modified Capabilities
<!-- None — this is purely additive. -->

## Impact

- `scripts/batch_generate.py`: new `--prompts` flag and a post-processing step
  that reads `qa_items.jsonl`, groups items by topology+seed, and writes paired
  `.md` files.
- No changes to pipeline stages, templates, simulation, or QA generation.
- No new dependencies.
