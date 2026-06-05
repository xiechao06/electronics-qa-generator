## ADDED Requirements

### Requirement: RichnessScore data class
The system SHALL define a `RichnessScore` dataclass with numeric fields `total` (0.0–1.0), `separability`, `stability`, and `probe_coverage`.

### Requirement: Score computation
The system SHALL provide `compute_richness(facts: dict, sim_result: SimResult) -> RichnessScore`. The initial implementation SHALL return a neutral score (0.5 for all fields) with `probe_coverage` set to 1.0 if all declared probes produced data, 0.0 otherwise.

#### Scenario: Successful simulation scores neutral
- **WHEN** `compute_richness` is called with facts from a successful simulation
- **THEN** `total` is 0.5 and `probe_coverage` is 1.0

#### Scenario: Failed simulation scores zero
- **WHEN** `compute_richness` is called with `sim_result.success == False`
- **THEN** `total` is 0.0 and all sub-scores are 0.0

### Requirement: Future extensibility
The `compute_richness` function signature SHALL accept an optional `all_samples: list[dict] | None` parameter for future comparison-based separability scoring. When `None`, the current neutral behavior is used.
