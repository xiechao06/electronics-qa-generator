## ADDED Requirements

### Requirement: Standalone validate command

The `eqa` CLI SHALL provide a `validate` subcommand that accepts topology, seed, and
optional flags (--list, --json) and runs all static checks on generated QA items,
printing the validation report.

#### Scenario: Basic validate run

- **WHEN** `eqa validate voltage_divider --seed 42` runs
- **THEN** QA items are generated, static checks run, and the report is printed

#### Scenario: List available topologies

- **WHEN** `eqa validate --list` runs
- **THEN** available topology names are printed

#### Scenario: JSON output

- **WHEN** `eqa validate voltage_divider --json` runs
- **THEN** the validation report is printed as a JSON object

### Requirement: Opt-in verify flag on questions

The `eqa questions` command SHALL accept a `--verify` flag that runs the static
verifier on generated items before output and includes the verification status
in the result.

#### Scenario: Questions with verify

- **WHEN** `eqa questions voltage_divider --verify` runs
- **THEN** each item's output includes a `verified: true/false` field
- **AND** FAIL items carry a `verification_errors` field listing violated checks

### Requirement: Exit code reflects verification

The `eqa validate` command SHALL exit with code 0 when all checks pass and code 1
when any FAIL verdict exists, enabling use as a CI gate.

#### Scenario: Exit 0 on all-pass

- **WHEN** `eqa validate` runs and all checks pass
- **THEN** the process exits with code 0

#### Scenario: Exit 1 on any fail

- **WHEN** `eqa validate` runs and at least one FAIL verdict exists
- **THEN** the process exits with code 1
