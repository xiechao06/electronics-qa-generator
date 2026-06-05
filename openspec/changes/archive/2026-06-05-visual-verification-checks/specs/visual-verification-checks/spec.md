## ADDED Requirements

### Requirement: Visual check integration

Visual checks SHALL be opt-in via `--visual` flag and SHALL require the schematic
PNG to exist (produced by `--render`). When no PNG exists, checks SHALL return PASS.

#### Scenario: Visual checks run when PNG available

- **WHEN** `eqa validate rc_lowpass --render --visual` runs
- **THEN** two visual checks execute on the rendered schematic

#### Scenario: Visual checks skipped when no PNG

- **WHEN** `--visual` is set but `--render` was not used
- **THEN** visual checks return PASS with message "no schematic to check"

### Requirement: VLM unavailability pass-through

When the VLM is not running (Ollama not started, model not pulled), visual checks
SHALL return PASS without blocking the pipeline.

#### Scenario: Ollama not running

- **WHEN** `--visual` is set but Ollama is not running on localhost:11434
- **THEN** checks return PASS with "VLM unavailable" message
