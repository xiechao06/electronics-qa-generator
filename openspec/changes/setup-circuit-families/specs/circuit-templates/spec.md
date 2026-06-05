## ADDED Requirements

### Requirement: Voltage divider template
The system SHALL provide a `VoltageDivider` template that samples two resistor values (`R1`, `R2`) from the E12 series between 100Ω and 1MΩ, a DC supply voltage between 1V and 30V, and emits an `.op` netlist probing the divider output node. The `CircuitRecord.difficulty` SHALL be 1.

#### Scenario: Sample produces valid voltage divider
- **WHEN** `VoltageDivider().sample(seed=42)` is called
- **THEN** the returned `CircuitRecord` has `family="passive"`, `topology="voltage_divider"`
- **AND** `parameters` contains keys `R1_ohm`, `R2_ohm`, `Vin_dc` with numeric values
- **AND** `netlist` is a non-empty string containing `R1`, `R2`, `Vin`, `.op`, and `.end`
- **AND** `simulation.type` is `"op"`
- **AND** `probes` includes at least `V(out)`

#### Scenario: Multiple samples vary
- **WHEN** `VoltageDivider().sample()` is called three times with different seeds
- **THEN** at least one of `R1_ohm`, `R2_ohm`, or `Vin_dc` differs between calls

### Requirement: RC low-pass filter template
The system SHALL provide an `RCLowPass` template that samples one resistor (E12, 1kΩ to 1MΩ) and one capacitor (E6, 100pF to 10μF), emits an `.ac` netlist sweeping from 1Hz to 10MHz with 50 points per decade, probed at the output node. The `CircuitRecord.difficulty` SHALL be 1.

#### Scenario: Sample produces valid RC low-pass netlist
- **WHEN** `RCLowPass().sample(seed=42)` is called
- **THEN** the returned `CircuitRecord` has `family="passive"`, `topology="rc_lowpass"`
- **AND** `parameters` contains `R1_ohm` and `C1_f` with numeric values
- **AND** `netlist` contains `R1`, `C1`, `AC 1`, `.ac dec 50`, and `.end`
- **AND** `simulation.type` is `"ac"`
- **AND** `simulation.params` contains `start_hz`, `stop_hz`, `points_per_decade`
- **AND** `probes` includes `V(out)`

#### Scenario: AC sweep range is wide enough to capture cutoff
- **WHEN** `RCLowPass().sample()` is called for any parameters in range
- **THEN** the theoretical cutoff frequency `1/(2π·R·C)` SHALL fall within `start_hz` and `stop_hz`

### Requirement: RC high-pass filter template
The system SHALL provide an `RCHighPass` template that samples one resistor (E12, 1kΩ to 1MΩ) and one capacitor (E6, 100pF to 10μF), emits an `.ac` netlist sweeping from 1Hz to 10MHz, probed at the output node. The `CircuitRecord.difficulty` SHALL be 1.

#### Scenario: Sample produces valid RC high-pass netlist
- **WHEN** `RCHighPass().sample(seed=42)` is called
- **THEN** the returned `CircuitRecord` has `family="passive"`, `topology="rc_highpass"`
- **AND** the netlist SHALL have the resistor and capacitor in a high-pass topology (capacitor in series with input, resistor to ground)
- **AND** `simulation.type` is `"ac"`

### Requirement: RLC band-pass filter template
The system SHALL provide an `RLCBandPass` template that samples one resistor (E12, 100Ω to 10kΩ), one inductor (selected values 1mH to 100mH), and one capacitor (E6, 10nF to 1μF), emits an `.ac` netlist sweeping from 10Hz to 10MHz, probed at the output node. The `CircuitRecord.difficulty` SHALL be 1.

#### Scenario: Sample produces valid RLC band-pass netlist
- **WHEN** `RLCBandPass().sample(seed=42)` is called
- **THEN** the returned `CircuitRecord` has `family="passive"`, `topology="rlc_bandpass"`
- **AND** `parameters` contains `R1_ohm`, `L1_h`, `C1_f`
- **AND** the netlist SHALL have the resistor, inductor, and capacitor in a series RLC topology with output across R
- **AND** `simulation.type` is `"ac"`

### Requirement: Half-wave rectifier template
The system SHALL provide a `HalfWaveRectifier` template that samples a load resistor (E12, 1kΩ to 100kΩ), a filter capacitor (E6, 1μF to 100μF), and an AC source amplitude (1V to 20V at 60Hz), emits a `.tran` netlist with at least 10 source periods and a suitable time step, probed at the output node. A default silicon diode model (e.g., `1N4148`) SHALL be used. The `CircuitRecord.difficulty` SHALL be 1.

#### Scenario: Sample produces valid half-wave rectifier netlist
- **WHEN** `HalfWaveRectifier().sample(seed=42)` is called
- **THEN** the returned `CircuitRecord` has `family="diode"`, `topology="half_wave_rectifier"`
- **AND** `parameters` contains `R_load_ohm`, `C_filter_f`, `Vin_amplitude`
- **AND** the netlist contains `D1`, the diode model, `.tran`, and `.end`
- **AND** `simulation.type` is `"tran"`
- **AND** `simulation.params` contains `stop_time` and `time_step`

#### Scenario: Transient simulation captures steady state
- **WHEN** `HalfWaveRectifier().sample()` is called
- **THEN** the `stop_time` in `simulation.params` SHALL be at least 10 times the source period (≥ ~167ms for 60Hz)

### Requirement: All templates expose a registry
The system SHALL provide a module-level list `ALL_TEMPLATES` that contains one instance of each concrete template class. This list SHALL serve as the entry point for the downstream sampler stage.

#### Scenario: Registry contains all five templates
- **WHEN** `from electronics_qa_generator.templates import ALL_TEMPLATES` is executed
- **THEN** `ALL_TEMPLATES` is a list containing exactly 5 items
- **AND** each item is a concrete `CircuitTemplate` instance with distinct `topology` values

### Requirement: Deterministic reproducibility
Every template's `sample()` method SHALL be fully deterministic: given the same seed, `sample()` MUST return a `CircuitRecord` with identical `parameters`, `netlist`, and every populated field. This SHALL hold across process invocations.

#### Scenario: Same seed produces identical output
- **WHEN** `template.sample(seed=42)` is called twice (possibly in separate Python processes)
- **THEN** `record1.netlist == record2.netlist` and `record1.parameters == record2.parameters`

#### Scenario: Different seeds produce different output
- **WHEN** `template.sample(seed=42)` and `template.sample(seed=43)` are compared
- **THEN** at least one parameter or netlist detail differs between the two records
