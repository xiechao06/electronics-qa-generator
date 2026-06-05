## ADDED Requirements

### Requirement: BJT emitter follower template

The system SHALL provide a `CircuitTemplate` subclass for an NPN BJT
common-collector stage. Sample VCC (5–15 V), RE (E12), and β. Emit `.op` +
`.ac` netlists.

#### Scenario: Gain near unity
- **WHEN** emitter follower is simulated
- **THEN** 0.9 < A_v < 1.0

### Requirement: Fact extractor outputs r_out, A_v, V_CEQ

Extract `r_out_ohm`, `A_v`, `V_CEQ` from simulation output.

### Requirement: 3 question templates activated

Move emitter follower templates into `QUESTION_TEMPLATES["bjt_emitter_follower"]`.

### Requirement: SVG schematic — no disconnected components
