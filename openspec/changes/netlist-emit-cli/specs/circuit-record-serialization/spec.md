## ADDED Requirements

### Requirement: Serialize CircuitRecord to a JSON-compatible dict
The system SHALL provide a function `record_to_dict(record: CircuitRecord) -> dict` that returns a JSON-compatible dictionary containing the fields `id`, `family`, `topology`, `difficulty`, `parameters`, `netlist`, `simulation`, and `probes`. The nested `SimulationConfig` SHALL be represented as a dict with keys `type`, `tool`, and `params`. When `record.simulation` is `None`, the `simulation` key SHALL be `None`.

#### Scenario: Record fields are present in the dict
- **WHEN** `record_to_dict` is called on a sampled `CircuitRecord`
- **THEN** the returned dict contains all of `id`, `family`, `topology`, `difficulty`, `parameters`, `netlist`, `simulation`, `probes`
- **AND** `parameters` is a dict of the sampled numeric values
- **AND** `probes` is a list of strings

#### Scenario: Nested simulation config is flattened
- **WHEN** `record_to_dict` is called on a record whose `simulation` is a `SimulationConfig(type="ac", tool="Xyce", params={...})`
- **THEN** `result["simulation"]` is a dict equal to `{"type": "ac", "tool": "Xyce", "params": {...}}`

#### Scenario: Missing simulation serializes as None
- **WHEN** `record_to_dict` is called on a record with `simulation=None`
- **THEN** `result["simulation"]` is `None`

### Requirement: Serialize CircuitRecord to a JSON string
The system SHALL provide a function `record_to_json(record: CircuitRecord, *, indent: int = 2) -> str` that returns a string of valid JSON. The string MUST be parseable by `json.loads` back into a dict equal to `record_to_dict(record)`.

#### Scenario: Output is valid parseable JSON
- **WHEN** `record_to_json` is called on a sampled record
- **THEN** `json.loads(result)` succeeds
- **AND** the parsed object equals `record_to_dict(record)`

#### Scenario: Deterministic output for same record
- **WHEN** `record_to_json` is called twice on records sampled from the same template with the same seed
- **THEN** the two JSON strings are identical
