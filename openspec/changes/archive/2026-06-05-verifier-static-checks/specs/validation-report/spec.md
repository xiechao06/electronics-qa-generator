## ADDED Requirements

### Requirement: Per-item verdicts

The `ValidationReport` SHALL associate each `QAItem` with a verdict of PASS, FAIL, or
WARN for each check that was run, and SHALL provide a human-readable message explaining
each non-PASS verdict.

#### Scenario: Single item with multiple checks

- **WHEN** a QA item is verified with 7 checks, all passing
- **THEN** the report lists 7 PASS verdicts for that item

#### Scenario: Item with one FAIL and one WARN

- **WHEN** a QA item triggers a FAIL on tolerance check and a WARN on leakage check
- **THEN** the report records both verdicts with explanatory messages

### Requirement: Aggregate statistics

The report SHALL compute aggregate statistics: total items, total checks, count
breakdown by verdict (PASS / FAIL / WARN), and a list of FAIL verdicts with item
indices for quick identification.

#### Scenario: Aggregate on a batch run

- **WHEN** 5 items × 7 checks = 35 total checks run
- **THEN** the aggregate shows counts like `{PASS: 32, FAIL: 2, WARN: 1}`

### Requirement: Serialization

The report SHALL be serializable to JSON for CI integration and SHALL include a
top-level `ok: bool` field (true when zero FAIL verdicts exist).

#### Scenario: All pass

- **WHEN** all checks pass
- **THEN** the serialized JSON has `"ok": true`

#### Scenario: Any FAIL

- **WHEN** one or more checks fail
- **THEN** the serialized JSON has `"ok": false`
