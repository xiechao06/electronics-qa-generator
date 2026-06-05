## Why

7 of 14 circuit topologies have placeholder fact extractors returning all-zero
answers. Write proper extractors for each so all 63 question templates produce
accurate, simulator-grounded answers.

## What Changes

- Write 7 new extractor functions in `extraction/facts.py`
- Update BJT/MOSFET/op-amp templates to emit `.op` directive for bias extraction
- Fix fact keys to match question template expectations

## Impact

- `extraction/facts.py` — 7 new extractors + registry updates
- `templates/bjt.py`, `templates/mosfet.py`, `templates/op_amp.py` — add .op
