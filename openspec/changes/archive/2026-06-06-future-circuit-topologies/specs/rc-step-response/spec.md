## ADDED Requirements

### Requirement: Circuit template generates valid Xyce netlist

The system SHALL provide a `CircuitTemplate` subclass that samples RC component
values (R from E12, C from E6), constructs a series RC circuit with step-input
voltage source (PWL), emits a valid `.tran` SPICE netlist, and returns a
`CircuitRecord` with graph, parameters, and simulation config.

#### Scenario: Sample produces reproducible circuit

- **WHEN** `RCStepResponse().sample(seed=0)` is called twice
- **THEN** both calls produce identical netlists and parameter dicts

#### Scenario: Simulation converges

- **WHEN** the emitted netlist is run through Xyce with `.tran`
- **THEN** the simulation converges and produces capacitor voltage waveform data

### Requirement: Fact extractor computes canonical facts

The system SHALL parse `.tran` output and extract `tau_s`, `v_C_initial`,
`v_C_final`, and `v_C_at_1tau` from the capacitor voltage waveform.

#### Scenario: Time constant matches theoretical value

- **WHEN** R=1kΩ and C=1μF (theoretical τ = 1 ms)
- **THEN** the extracted `tau_s` is within 1% of 0.001

### Requirement: Question templates are activated

The system SHALL move the 5 RC step response question templates from
`future_templates.py` into `QUESTION_TEMPLATES["rc_step_response"]` in
`templates.py`, producing valid QA items with computed answers.

#### Scenario: All 5 templates generate answers

- **WHEN** `generate_questions("rc_step_response", facts, params)` is called
- **THEN** 5 QA items are returned with non-None answers and programs

### Requirement: SVG schematic has fully connected wires

The system SHALL provide an SVG layout template for the RC step response
circuit with all wire segments sharing exact endpoint coordinates at
junctions and leads touching symbol boundaries (no gaps).

#### Scenario: SVG renders without disconnections

- **WHEN** the SVG is validated for endpoint connectivity
- **THEN** every non-symbol-interior endpoint appears at least twice
  across all wire/sym elements
