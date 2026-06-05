## ADDED Requirements

### Requirement: BJT CE amplifier template with self-biasing

The system SHALL provide a `CircuitTemplate` subclass that constructs a
self-biased BJT common-emitter stage (R1, R2, RC, RE, bypass capacitor),
samples β ∈ {100, 150, 200, 300}, uses 2N2222 model parameters, and emits
`.op` (bias) + `.ac` (gain) netlists.

#### Scenario: Bias point is in active region
- **WHEN** the circuit is simulated with typical resistor values
- **THEN** V_CEQ > 1 V (transistor is in active region, not saturation)

### Requirement: Fact extractor computes bias and gain facts

The system SHALL extract `V_CEQ`, `I_CQ_mA`, `A_v`, `r_out_ohm`,
and `operating_region`.

#### Scenario: Gain is negative (inverting)
- **WHEN** small-signal gain A_v is computed
- **THEN** A_v < 0 (CE amplifier inverts)

### Requirement: 5 question templates activated

Move BJT CE templates into `QUESTION_TEMPLATES["bjt_ce_amplifier"]`.

### Requirement: SVG schematic — no disconnected components

SVG template with all wires connected end-to-end.
