## ADDED Requirements

### Requirement: List available templates
The system SHALL provide an `eqa emit --list` command that prints the topology name of every template in `ALL_TEMPLATES`, one per line, and exits with code 0.

#### Scenario: List prints all topologies
- **WHEN** `eqa emit --list` is run
- **THEN** the output contains the lines `voltage_divider`, `rc_lowpass`, `rc_highpass`, `rlc_bandpass`, and `half_wave_rectifier`
- **AND** the exit code is 0

### Requirement: Emit a single template to stdout
The system SHALL provide `eqa emit <topology> [--seed N]` that samples the named template with the given seed (default 0) and prints the netlist followed by a delimiter and the JSON record to stdout.

#### Scenario: Emit prints netlist and JSON
- **WHEN** `eqa emit rc_lowpass --seed 42` is run
- **THEN** the output contains the netlist text (starting with `*` and containing `.end`)
- **AND** the output contains a JSON object with `"topology": "rc_lowpass"`
- **AND** the exit code is 0

#### Scenario: Unknown topology errors with valid names
- **WHEN** `eqa emit not_a_circuit` is run
- **THEN** the command prints an error naming the invalid topology
- **AND** the error message lists the valid topology names
- **AND** the exit code is non-zero

### Requirement: Emit to an output directory
The system SHALL support `eqa emit <topology> --seed N -o DIR`, writing the netlist to `DIR/<topology>_<seed>.cir` and the JSON record to `DIR/<topology>_<seed>.json`. The directory SHALL be created if it does not exist.

#### Scenario: Files are written to the output directory
- **WHEN** `eqa emit rc_lowpass --seed 42 -o build/` is run
- **THEN** a file matching `build/rc_lowpass_*.cir` exists and contains the netlist
- **AND** a file matching `build/rc_lowpass_*.json` exists and contains valid JSON with `"topology": "rc_lowpass"`
- **AND** the exit code is 0

#### Scenario: Output directory is created when missing
- **WHEN** `eqa emit rc_lowpass -o newdir/sub/` is run and `newdir/sub/` does not exist
- **THEN** the directory is created
- **AND** the netlist and JSON files are written inside it

### Requirement: Emit all templates
The system SHALL support `eqa emit --all [--seed N] [-o DIR]`, which emits every template in `ALL_TEMPLATES`. When `-o DIR` is given, it writes one `.cir` and one `.json` file per template.

#### Scenario: Emit all writes a file pair per template
- **WHEN** `eqa emit --all --seed 7 -o build/` is run
- **THEN** `build/` contains a `.cir` and a `.json` file for each of the five templates
- **AND** the exit code is 0

### Requirement: Reproducible emission
Emission SHALL be reproducible: the same topology and seed MUST produce byte-identical netlist and JSON output across runs.

#### Scenario: Same seed yields identical files
- **WHEN** `eqa emit rc_lowpass --seed 42 -o a/` and `eqa emit rc_lowpass --seed 42 -o b/` are run
- **THEN** the `.cir` files in `a/` and `b/` are byte-identical
- **AND** the `.json` files in `a/` and `b/` are byte-identical
