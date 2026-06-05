## ADDED Requirements

### Requirement: Series RLC resonance template

The system SHALL provide a `CircuitTemplate` subclass for series RLC with
AC frequency sweep. Sample R (E12, decades 1–3), L (standard values), C (E6).
Emit `.ac` netlist sweeping 10 Hz – 10 MHz.

#### Scenario: Resonance detected
- **WHEN** the AC sweep covers the resonant frequency range
- **THEN** a clear resonant peak is detected with Q > 0.5

### Requirement: Fact extractor computes resonance facts

Extract `f_r_hz`, `Q`, `bandwidth_hz`, `Z_at_resonance_ohm`, `R_ohm`.

#### Scenario: Impedance at resonance approaches R
- **WHEN** Z_at_resonance_ohm is extracted
- **THEN** |Z_at_resonance_ohm − R_ohm| / R_ohm < 0.05

### Requirement: 4 question templates activated

Move resonance templates into `QUESTION_TEMPLATES["rlc_series_resonance"]`.

### Requirement: SVG schematic — no disconnected components
