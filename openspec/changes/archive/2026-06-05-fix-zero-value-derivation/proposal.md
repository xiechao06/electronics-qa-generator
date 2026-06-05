## Why

Voltage divider "ratio" and "percentage" derived questions compute to 0.0 instead
of the actual ratio (e.g., 7.586 / 8.102 = 0.936). The bug: `read_fact("Vin_dc")`
fails because `Vin_dc` is a circuit **parameter** not a simulation fact — the
extractor stores only `Vout_dc` and `divider_ratio` in facts. The program should
use `read_param("Vin_dc")` to read from the parameter dict.

## What Changes

- Fix the two voltage-divider derived question programs to use `read_param` instead
  of `read_fact` for `Vin_dc`.
- Add `Vin_dc` to the voltage divider fact extractor's output dict so both
  `read_fact` and `read_param` can access it.

## Impact

- `questions/templates.py`: 2 program lines changed
- `extraction/facts.py`: 1 line added to extractor
