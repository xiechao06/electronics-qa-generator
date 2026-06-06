## 1. Implementation

- [x] 1.1 In `_generate_prompt_files` in `scripts/batch_generate.py`, after
  writing the numbered answers, append a `## Netlist` section with the SPICE
  netlist (from the first item in the group's `netlist` field) inside a fenced
  code block.

## 2. Verification

- [x] 2.1 Run `uv run python scripts/batch_generate.py --total 200 --workers 8
  -o output/batch --prompts` and verify every answer file ends with a
  `## Netlist` section containing the SPICE netlist.
