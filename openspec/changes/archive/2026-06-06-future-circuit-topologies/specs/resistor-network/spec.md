## ADDED Requirements

### Requirement: Resistor network template with Thevenin extraction

The system SHALL provide a `CircuitTemplate` subclass that constructs a
multi-resistor DC network with one voltage source (5–30 V) and 4–6 resistors
(E12 values). Emit `.op` netlist with test sources for R_th measurement.

#### Scenario: Thevenin equivalent is consistent
- **WHEN** V_th and R_th are extracted
- **THEN** V_th / (R_th + R_load) matches simulated load voltage within 1%

### Requirement: Fact extractor computes network facts

Extract `R_eq_ohm`, `V_th_V`, `R_th_ohm`, `P_source_W`.

### Requirement: 5 question templates activated

Move resistor network templates into `QUESTION_TEMPLATES["resistor_network"]`.

### Requirement: SVG schematic — no disconnected components
