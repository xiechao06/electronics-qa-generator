## ADDED Requirements

### Requirement: Op-amp inverting amplifier template

The system SHALL provide a `CircuitTemplate` subclass using an ideal op-amp
model (VCVS E-element, gain=1e5, R_in=1MΩ, R_out=75Ω). Sample Rf, Rin from E12.
Emit `.op` + `.ac` netlists.

#### Scenario: Closed-loop gain matches −Rf/Rin
- **WHEN** Rf=10kΩ and Rin=1kΩ
- **THEN** |A_v + 10| < 0.1 (gain is approximately −10)

### Requirement: Fact extractor outputs gain and bandwidth

Extract `A_v`, `V_out_dc`, `f_3dB_hz`, `configuration="inverting"`.

### Requirement: 4 question templates activated

Move op-amp templates into `QUESTION_TEMPLATES["op_amp_inverting"]`.

### Requirement: SVG schematic — no disconnected components
