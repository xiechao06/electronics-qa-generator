## ADDED Requirements

### Requirement: Answer recomputation check

The verifier SHALL recompute the answer from stored facts using the item's CLEVR-style
program and SHALL assert byte-for-byte equality with the stored answer. A mismatch
SHALL result in a FAIL verdict.

#### Scenario: Correct answer passes

- **WHEN** a QA item with a correct program is verified
- **THEN** the recomputed answer matches the stored answer and the check returns PASS

#### Scenario: Mismatched answer fails

- **WHEN** the recomputed answer differs from the stored answer
- **THEN** the check returns FAIL with details of the difference

### Requirement: Parameter consistency check

The verifier SHALL verify that component values (R, C, L) mentioned in the question
text are consistent with the values in the circuit's parameter dict. Any value present
in the question that differs from the corresponding parameter SHALL trigger a FAIL.

#### Scenario: All parameter values match

- **WHEN** question mentions "R = 6.8k Ω" and params has `R1_ohm: 6800.0`
- **THEN** the check returns PASS

#### Scenario: Parameter value mismatch

- **WHEN** question mentions "R = 10k Ω" but params has `R1_ohm: 6800.0`
- **THEN** the check returns FAIL

#### Scenario: No parameter placeholders in question

- **WHEN** the question text does not reference any component values
- **THEN** the check returns PASS (no mismatch possible)

### Requirement: Unit consistency check

The verifier SHALL detect when the unit referred to in the question text differs from
the answer's stored unit. The check SHALL compare the expected answer unit (from the
format_numeric program step) with any unit mentioned in the question text.

#### Scenario: Unit matches

- **WHEN** question asks for answer in "Hz" and answer unit is "Hz"
- **THEN** the check returns PASS

#### Scenario: Unit mismatch

- **WHEN** question asks "Provide your answer in kHz" but answer unit is "Hz"
- **THEN** the check returns FAIL

### Requirement: Literal answer leakage check

The verifier SHALL use regex to detect when the numeric answer value or answer string
appears verbatim in the question text. Detection SHALL result in a WARN verdict (not
FAIL, since some question formats legitimately reference the answer, e.g., MC choices).

#### Scenario: Answer not leaked

- **WHEN** question text is "Find the cutoff frequency." and answer is "233 Hz"
- **THEN** the check returns PASS

#### Scenario: Answer leaked in question

- **WHEN** question text contains the literal answer value "233 Hz" or numeric "233"
- **THEN** the check returns WARN with the detected substring

### Requirement: Degenerate value detection

The verifier SHALL flag QA items whose answer_value is NaN, ±inf, or whose magnitude
is implausible for the expected unit (e.g., frequency values of 0.0 or excess of
1e12 Hz for a passive filter). Degenerate values SHALL trigger a FAIL.

#### Scenario: Normal value passes

- **WHEN** answer_value is 233.5 with unit "Hz"
- **THEN** the check returns PASS

#### Scenario: Zero frequency fails

- **WHEN** answer_value is 0.0 with unit "Hz" for a cutoff frequency question
- **THEN** the check returns FAIL

#### Scenario: NaN value fails

- **WHEN** answer_value is NaN
- **THEN** the check returns FAIL

### Requirement: Tolerance appropriateness

The verifier SHALL reject tolerances that exceed 50% of the answer magnitude (for
non-zero values) and SHALL flag tolerances smaller than 1e-12 as suspicious.

#### Scenario: Reasonable tolerance passes

- **WHEN** answer_value is 233.5 and tolerance is 0.5
- **THEN** the check returns PASS

#### Scenario: Excessive tolerance fails

- **WHEN** answer_value is 233.5 and tolerance is 200 (86% of magnitude)
- **THEN** the check returns FAIL

#### Scenario: Near-zero value with small absolute tolerance passes

- **WHEN** answer_value is -9e-9 and tolerance is 0.005
- **THEN** the check returns PASS (absolute tolerance is reasonable regardless of relative ratio)

### Requirement: Template coverage check

The verifier SHALL assert that a batch of QA items from a single topology includes at
least 2 distinct question types and that no two items sharing the same template ID
produce identical question text across different seeds.

#### Scenario: Good coverage passes

- **WHEN** 5 voltage_divider items include types: direct, direct, derived, derived,
  comparison
- **THEN** the check returns PASS

#### Scenario: Single question type fails

- **WHEN** all 5 items from a topology are type "direct"
- **THEN** the check returns FAIL
