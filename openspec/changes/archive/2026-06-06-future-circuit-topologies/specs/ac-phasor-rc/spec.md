## ADDED Requirements

### Requirement: Circuit template generates valid Xyce netlist

The system SHALL provide a `CircuitTemplate` subclass that samples R (E12),
C (E6), and a single-frequency sinusoidal source, emits a valid single-point
`.ac` SPICE netlist.

#### Scenario: Single-frequency AC sweep
- **WHEN** source frequency is set to 1 kHz
- **THEN** the netlist includes `.ac lin 1 1000 1000`

### Requirement: Fact extractor computes phasor facts

The system SHALL parse `.ac` output and extract `V_C_mag_V`, `V_C_phase_deg`,
`Z_mag_ohm`, `Z_phase_deg`, and `P_avg_mW`.

#### Scenario: Phase lag for RC circuit
- **WHEN** V_C phase is extracted from simulation
- **THEN** `V_C_phase_deg` is negative (capacitor voltage lags source)

### Requirement: Question templates are activated

The system SHALL move 5 AC phasor templates into
`QUESTION_TEMPLATES["ac_phasor_rc"]`.

#### Scenario: All 5 templates generate answers
- **WHEN** `generate_questions("ac_phasor_rc", facts, params)` is called
- **THEN** 5 QA items are returned

### Requirement: SVG schematic has fully connected wires

The system SHALL provide an SVG layout template with all wire endpoints
fully connected.
