## Context

The pipeline currently has no automated quality gate. Bugs (zero-value derived
answers, answer leakage in classification questions) were caught by manual review.
The architecture §11 reserves a Verifier stage with a clear mandate: check items for
correctness, consistency, and quality before they enter the dataset.

This change implements the **static** tier of the Verifier — 7 checks that run
deterministically without LLM involvement. Each check is a pure function of `QAItem` +
facts + parameters, making them fast, parallelizable, and suitable as a CI gate.

## Goals / Non-Goals

**Goals:**
- Catch regressions: answer drift, parameter mismatch, unit confusion, leakage.
- Provide structured, machine-readable verdicts (JSON) for CI integration.
- Zero new dependencies — pure Python checks only.
- Opt-in via `eqa validate` (standalone) and `--verify` on `eqa questions`.

**Non-Goals:**
- LLM-assisted checks (wording ambiguity, semantic leakage, difficulty scoring).
- Visual checks (schematic–topology match, label readability).
- Auto-fixing detected issues; the verifier only reports.

## Decisions

### Decision: Check functions return `CheckResult` dataclass
Each check is a function `check_*(item, facts, params) -> CheckResult` with fields
`name: str`, `verdict: Verdict`, `message: str`. Verdict is an enum: PASS, FAIL, WARN.
- **Why:** Uniform interface makes it trivial to add new checks. The report aggregates
  results without knowing check-specific details.
- **Alternative considered:** Exceptions per check. Rejected — harder to aggregate,
  and we want to run ALL checks even if some fail.

### Decision: Verifier runs after question generation, before output
In `run_questions` and `run_validate`, items are generated → verified → emitted. The
verifier observes but never modifies items, preserving the invariant that facts flow
one way.
- **Why:** The verifier is a quality gate, not a corrective step. It shouldn't alter
  data.

### Decision: Separate `eqa validate` subcommand
A dedicated `validate` subcommand wraps the full pipeline but prints only the report.
The `--verify` flag on `questions` is lighter-weight: it embeds verification status
in the existing output.
- **Why:** Two use cases — CI runs `validate` for a pass/fail summary; ad-hoc
  debugging uses `questions --verify` to see per-item details inline.

### Decision: Tolerance check uses absolute tolerance for near-zero values
Values with magnitude < 1e-6 are checked against an absolute tolerance floor (0.01)
rather than a relative ratio. This avoids the "52 million%" false positive seen with
passband gain.
- **Why:** Engineering measurements near zero (e.g., −0.00 dB gain) have meaningful
  absolute tolerances but meaningless relative ones.

### Decision: Parameter consistency uses regex on formatted values
Rather than parsing the question text for component values with full NLP, we take the
formatted parameter values (from `_fmt_resistance`, etc.) and check if they appear in
the question as substrings. This is O(n) and robust.
- **Alternative considered:** Full parser. Rejected — too fragile for the benefit;
  substring match catches the common cases reliably.

## Risks / Trade-offs

- **Regex false positives on leakage** → Leakage is WARN-level, not FAIL. False
  positives are acceptable noise.
- **Parameter check misses values in different notation** → If the question formats
  "6.8k Ω" but params has 6800, the check depends on the format_map filling. Since we
  use the same formatters as the question template, this is consistent.
- **Unit check is approximate** → We compare the expected unit from `format_numeric`
  against units found in the question text. Handles common cases (Hz vs kHz) but not
  every edge.

## Migration Plan

1. Add `validation/checks.py` (7 check functions + CheckResult).
2. Add `validation/report.py` (ValidationReport model).
3. Add `validation/cli_handler.py` (run_validate).
4. Add `eqa validate` subcommand to `cli.py`.
5. Add `--verify` flag to `eqa questions`.
6. Add tests (~20).
7. Document usage.
- **Rollback:** Remove the `validate` subcommand and `--verify` flag.

## Open Questions

- Exact degenerate-value thresholds per unit (frequency, voltage, etc.) — start with
  reasonable defaults (freq < 0 or > 1e9, voltage < -1e3 or > 1e6) and tune later.
