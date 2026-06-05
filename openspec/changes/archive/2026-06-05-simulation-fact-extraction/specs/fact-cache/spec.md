## ADDED Requirements

### Requirement: Cache store and retrieve facts
The system SHALL provide a `FactCache` class with `get(topology: str, seed: int) -> dict | None` and `put(topology: str, seed: int, facts: dict) -> None` methods. Facts SHALL be stored as JSON files named `<topology>_<seed:08x>.json` in a configurable cache directory.

#### Scenario: Cache miss returns None
- **WHEN** `get` is called for a topology/seed not previously cached
- **THEN** `None` is returned

#### Scenario: Cache hit returns stored facts
- **WHEN** `put` stores a fact dict and `get` is called with the same key
- **THEN** the returned dict matches the stored dict exactly

#### Scenario: Cache files are valid JSON
- **WHEN** a fact dict is stored via `put`
- **THEN** the corresponding cache file is parseable by `json.load`

### Requirement: Configurable cache directory
The `FactCache` SHALL accept a `cache_dir: Path` at construction, defaulting to `.cache/eqa/` in the current working directory. The directory SHALL be created if it does not exist.

#### Scenario: Cache directory is auto-created
- **WHEN** `FactCache` is constructed with a non-existent directory
- **THEN** the directory is created on first `put`
