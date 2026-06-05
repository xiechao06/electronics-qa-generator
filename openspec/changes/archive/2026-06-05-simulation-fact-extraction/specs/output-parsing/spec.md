## ADDED Requirements

### Requirement: Parse .op output
The system SHALL provide `parse_op(raw_output: str) -> dict[str, float]` that parses Xyce `.print op` output into a dictionary mapping probe names (e.g., `"V(out)"`) to numeric values. Extra whitespace, header lines, and separator lines SHALL be ignored.

#### Scenario: Parse single-probe OP output
- **WHEN** `parse_op` is called with output containing `V(out) = 6.28319`
- **THEN** the returned dict contains `{"V(out)": 6.28319}`

#### Scenario: Parse multi-probe OP output
- **WHEN** `parse_op` receives output with two probes `V(out)` and `V(in)`
- **THEN** the returned dict contains both entries

### Requirement: Parse .ac output
The system SHALL provide `parse_ac(raw_output: str) -> dict[str, list[tuple[float, float]]]` that parses Xyce `.print ac` output into per-probe frequency-response data. Each probe's data is a list of `(frequency_hz, magnitude_db)` tuples. Phase data may be included if available.

#### Scenario: Parse AC sweep output
- **WHEN** `parse_ac` is called with a 3-point AC sweep of `V(out)`
- **THEN** the result contains `"V(out)"` key with 3 `(freq, mag)` tuples in ascending frequency order

### Requirement: Parse .tran output
The system SHALL provide `parse_tran(raw_output: str) -> dict[str, list[tuple[float, float]]]` that parses Xyce `.print tran` output into per-probe time-series data. Each probe's data is a list of `(time_s, value)` tuples.

#### Scenario: Parse transient output
- **WHEN** `parse_tran` is called with transient output for `V(out)` and `V(in)`
- **THEN** the result contains both keys with time-series data

### Requirement: Graceful failure on malformed input
Parsers SHALL return an empty dict (or an empty list for sweep probes) if the input cannot be parsed, rather than raising an exception. This allows the pipeline to continue with partial data.

#### Scenario: Malformed OP output returns empty dict
- **WHEN** `parse_op` receives a string with no parseable probe-value pairs
- **THEN** the result is an empty dict
