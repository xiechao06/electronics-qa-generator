## ADDED Requirements

### Requirement: MOSFET CS amplifier template

The system SHALL provide a `CircuitTemplate` subclass for an NMOS common-source
stage (R_D, R_S, R_G, V_DD). Use Xyce Level=1 NMOS model with sampled VTO and KP.
Emit `.op` + `.ac` netlists.

#### Scenario: Drain current within expected range
- **WHEN** V_DD=15 V, R_D=10kΩ, R_S=1kΩ
- **THEN** I_DQ is between 0.1 mA and 5 mA

### Requirement: Fact extractor outputs V_DSQ, I_DQ_mA, A_v

Extract `V_DSQ`, `I_DQ_mA`, `A_v` from simulation.

### Requirement: 3 question templates activated

Move MOSFET CS templates into `QUESTION_TEMPLATES["mosfet_cs_amplifier"]`.

### Requirement: SVG schematic — no disconnected components
