## 1. Core function

- [x] 1.1 Add `_generate_prompt_files(jsonl_path: Path, prompts_dir: Path) -> int`
  to `scripts/batch_generate.py`. It reads the JSONL, groups items by
  `(topology, seed)`, writes one `<topology>_<seed>.md` with numbered questions
  and image reference, and one `<topology>_<seed>_answers.md` with numbered
  answers (value + unit + tolerance). Returns the count of prompt/answer pairs
  written.
- [x] 1.2 Handle edge cases: empty JSONL (writes nothing, returns 0), missing
  `schematic_path` field (skips question gracefully), topology name with special
  characters (use as-is; the topology names are kebab-case already).

## 2. CLI integration

- [x] 2.1 Add `--prompts` flag to the `argparse` parser in `main()`.
- [x] 2.2 After the JSONL is finalized (both Phase 1 and optional Phase 2), call
  `_generate_prompt_files` when `--prompts` is set. Print a brief summary:
  "Wrote N prompt/answer pairs to <dir>".

## 3. Verification

- [x] 3.1 Run `uv run python scripts/batch_generate.py --total 200 --workers 8
  -o output/batch --prompts` and verify:
  - `output/batch/prompts/` exists
  - One `.md` and one `_answers.md` per (topology, seed) pair
  - Prompt file starts with image reference, lists numbered questions with no
    answers or netlist
  - Answer file has matching numbering with value + unit + tolerance
  - Existing output (`qa_items.jsonl`, `qa_items.yaml`, `images/`) is unchanged
- [x] 3.2 Verify that running without `--prompts` produces no `prompts/`
  directory.
