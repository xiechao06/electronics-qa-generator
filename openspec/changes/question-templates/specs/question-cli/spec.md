## ADDED Requirements

### Requirement: `eqa questions` subcommand
The system SHALL provide an `eqa questions` subcommand that accepts a topology name, runs the full pipeline (sample → simulate → extract facts → generate questions), and prints QA items as JSON to stdout.

#### Scenario: Generate questions for a single topology
- **WHEN** `eqa questions rc_lowpass --seed 42` is run and Xyce is available
- **THEN** the output is a JSON array of QAItem objects
- **AND** each item has `question_type`, `question`, `answer`, and `program` fields
- **AND** the exit code is 0

#### Scenario: List available topologies with question counts
- **WHEN** `eqa questions --list` is run
- **THEN** the output lists each topology and its number of question templates
- **AND** the exit code is 0

#### Scenario: Unknown topology error
- **WHEN** `eqa questions not_a_circuit` is run
- **THEN** the command prints an error and exits with non-zero code

### Requirement: CLI uses fact cache
The `eqa questions` command SHALL use the fact cache when `--no-cache` is not specified, avoiding re-simulation of previously sampled circuits.

#### Scenario: Cache hit skips simulation
- **WHEN** facts for `rc_lowpass` with `seed=42` are already cached
- **THEN** `eqa questions rc_lowpass --seed 42` uses the cached facts without invoking Xyce

### Requirement: `--jsonl` output mode
The `eqa questions` command SHALL support `--jsonl` flag that prints one JSON object per line instead of a JSON array.

#### Scenario: JSONL output is one object per line
- **WHEN** `eqa questions rc_lowpass --seed 42 --jsonl` is run
- **THEN** each line of stdout is a valid JSON object representing a single QAItem
