## ADDED Requirements

### Requirement: Circuit template generates valid Xyce netlist

The system SHALL provide a `CircuitTemplate` subclass that samples RL values
(L from standard inductor values, R from E12), constructs a series RL circuit
with step-input voltage source (PWL), emits a valid `.tran` SPICE netlist.

#### Scenario: Sample produces reproducible circuit
- **WHEN** `RLStepResponse().sample(seed=0)` is called twice
- **THEN** both calls produce identical netlists and parameter dicts

### Requirement: Fact extractor computes canonical facts

The system SHALL parse `.tran` output and extract `tau_s`, `i_L_initial`,
`i_L_final`, `i_L_at_1tau`, and `R_load_ohm`.

#### Scenario: Time constant equals L/R
- **WHEN** L=10mH and R=100Ω (theoretical τ = 0.1 ms)
- **THEN** the extracted `tau_s` is within 1% of 0.0001

### Requirement: Question templates are activated

The system SHALL move the 4 RL step response templates from `future_templates.py`
into `QUESTION_TEMPLATES["rl_step_response"]`.

#### Scenario: All 4 templates generate answers
- **WHEN** `generate_questions("rl_step_response", facts, params)` is called
- **THEN** 4 QA items are returned with non-None answers

### Requirement: SVG schematic has fully connected wires

The system SHALL provide an SVG layout template with all wire endpoints
connected at junctions and leads touching symbol boundaries.

#### Scenario: SVG renders without disconnections
- **WHEN** the SVG is validated for endpoint connectivity
- **THEN** no disconnected wire endpoints exist
