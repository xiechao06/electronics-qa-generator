## ADDED Requirements

### Requirement: Template base class defines sample contract
The system SHALL provide an abstract base class `CircuitTemplate` (subclass of `abc.ABC`) with class attributes `family` and `topology` (both `str`) and an abstract method `sample(seed: int | None = None) -> CircuitRecord`. Every concrete circuit template MUST inherit from `CircuitTemplate` and implement `sample()`.

#### Scenario: Concrete template implements sample
- **WHEN** a concrete template class (e.g. `RCLowPass`) inherits from `CircuitTemplate` and implements `sample()`
- **THEN** calling `sample()` returns a `CircuitRecord` with at minimum the fields `id`, `family`, `topology`, `parameters`, `netlist`, `simulation`, and `probes` populated
- **AND** `family` and `topology` match the template's class attributes

#### Scenario: Missing sample implementation raises error
- **WHEN** a class inherits from `CircuitTemplate` but does not implement `sample()`
- **THEN** instantiation raises `TypeError` (via ABC mechanism)

### Requirement: Parameter distributions support constrained randomization
The system SHALL provide distribution classes `Uniform(min, max)`, `LogUniform(min, max)`, and `Choice(values)` that each expose a `sample(rng: random.Random) -> float` method. Distributions MUST be deterministic: given the same `rng` state, `sample()` SHALL return the same value.

#### Scenario: Uniform distribution stays within bounds
- **WHEN** a `Uniform(1e3, 1e6)` distribution samples with a seeded `Random(42)`
- **THEN** every sample value is between `1e3` and `1e6` inclusive

#### Scenario: LogUniform distribution spans orders of magnitude
- **WHEN** a `LogUniform(1e-10, 1e-6)` distribution samples 1000 times with varying seeds
- **THEN** the sample values SHALL span at least 2 orders of magnitude

#### Scenario: Seeded sampling is deterministic
- **WHEN** two `random.Random` instances are created with the same seed and passed to the same distribution
- **THEN** `sample()` returns identical values for both

### Requirement: E-series value generation for standard components
The system SHALL provide helper functions that generate standard component values from E6 (capacitors) and E12 (resistors) series, given a decade range. Each function MUST return base values (e.g., 1.0, 1.5, 2.2, 3.3, 4.7, 6.8 for E6) that the caller can scale by a decade multiplier.

#### Scenario: E12 resistor values
- **WHEN** the E12 helper is queried
- **THEN** it returns the list `[1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]`

#### Scenario: E6 capacitor values
- **WHEN** the E6 helper is queried
- **THEN** it returns the list `[1.0, 1.5, 2.2, 3.3, 4.7, 6.8]`

### Requirement: Netlist emission binds parameters into valid Xyce syntax
The system SHALL provide a `format_netlist(template: str, params: dict) -> str` function that substitutes parameter placeholders (e.g., `{R1_ohm:.1f}`) into a SPICE netlist template string and returns a syntactically valid netlist. The function MUST handle numeric formatting for resistance (k suffix), capacitance (n/u/p suffixes), and frequency (k/Meg suffixes).

#### Scenario: Netlist contains substituted values
- **WHEN** a netlist template with placeholders `{R1_ohm:.1f}` and `{C1_f:.6e}` is formatted with `{"R1_ohm": 18200, "C1_f": 4.7e-9}`
- **THEN** the output contains `18.2k` and `4.7e-9` in the appropriate SPICE element lines

#### Scenario: Netlist header and footer are preserved
- **WHEN** a netlist template contains a comment header `* RC low-pass filter` and `.end` footer
- **THEN** the formatted output starts with the comment and ends with `.end`
