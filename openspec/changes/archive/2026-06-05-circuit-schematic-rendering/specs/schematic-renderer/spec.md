## ADDED Requirements

### Requirement: Render schematic from CircuitGraph

The system SHALL accept a `CircuitGraph` object and produce a PNG schematic image
where every component is drawn with a standard IEEE circuit symbol AND its value
(including unit) is clearly labeled next to the symbol. Each label SHALL show the
component's reference designator (R1, C1, L1, D1, V1) and its formatted value with
unit (e.g., "R1 10k Ω", "C1 100n F", "L1 10m H").

#### Scenario: Voltage divider schematic renders with values

- **WHEN** a `CircuitGraph` for a voltage divider (two resistors, one voltage source)
  is rendered
- **THEN** a PNG file is produced containing a zigzag line for each resistor and a
  circle with ± for the voltage source
- **AND** each resistor's label displays its reference designator and value+unit
  (e.g., "R1 4.7k Ω", "R2 10k Ω")
- **AND** the voltage source label displays its DC value (e.g., "V1 5V DC")

#### Scenario: RC low-pass filter schematic renders with capacitor value

- **WHEN** a `CircuitGraph` for an RC low-pass filter (one resistor, one capacitor,
  one AC voltage source) is rendered
- **THEN** the PNG shows a zigzag resistor with value+unit (e.g., "R1 1k Ω") and a
  parallel-plate capacitor with value+unit (e.g., "C1 100n F")

#### Scenario: RLC band-pass filter shows all three component values

- **WHEN** a `CircuitGraph` for an RLC band-pass filter (resistor, inductor,
  capacitor, AC source) is rendered
- **THEN** the PNG shows separate symbols for each, with labels displaying values:
  resistor in ohms (e.g., "R1 47 Ω"), inductor in henries (e.g., "L1 10m H"),
  capacitor in farads (e.g., "C1 1μ F")

#### Scenario: Half-wave rectifier renders diode and load with values

- **WHEN** a `CircuitGraph` for a half-wave rectifier is rendered
- **THEN** the PNG shows a diode as a triangle pointing to a bar with label
  (e.g., "D1 1N4148") and a resistor load with value+unit (e.g., "R_load 1k Ω")

### Requirement: Deterministic layout

The schematic renderer SHALL produce a deterministic, repeatable layout for each
topology. For a given `CircuitGraph`, the same PNG SHALL be produced on every run
(same component positions, same image dimensions).

#### Scenario: Two renders of the same graph are identical

- **WHEN** the same `CircuitGraph` is rendered twice with the same seed/parameters
- **THEN** the resulting PNG files are pixel-identical

### Requirement: Engineering-unit formatting on component labels

Every component SHALL display its value with an appropriate SI prefix and unit suffix.
The renderer SHALL format: resistors in Ω (kΩ, MΩ), capacitors in F (μF, nF, pF),
inductors in H (mH, μH), voltages in V (mV, kV), and frequencies in Hz (kHz, MHz).

#### Scenario: Resistor value formatting

- **WHEN** a resistor with value 4700 ohms is rendered
- **THEN** its label reads "R1 4.7k Ω" or "R1 4.7kΩ"

#### Scenario: Small resistor stays in ohms

- **WHEN** a resistor with value 47 ohms is rendered
- **THEN** its label reads "R1 47 Ω" or "R1 47Ω"

#### Scenario: Capacitor value formatting

- **WHEN** a capacitor with value 1e-7 farads is rendered
- **THEN** its label reads "C1 100n F" or "C1 100nF"

#### Scenario: Large capacitor formats in microfarads

- **WHEN** a capacitor with value 4.7e-6 farads is rendered
- **THEN** its label reads "C1 4.7μ F" or "C1 4.7μF"

#### Scenario: Inductor value formatting

- **WHEN** an inductor with value 0.01 henries is rendered
- **THEN** its label reads "L1 10m H" or "L1 10mH"

#### Scenario: Voltage source formatting

- **WHEN** a DC voltage source with value 5 volts is rendered
- **THEN** its label reads "V1 5V DC" and a ± symbol appears inside the source circle

#### Scenario: AC source formatting

- **WHEN** an AC voltage source with amplitude 1 V at 60 Hz is rendered
- **THEN** its label reads something like "V1 1V AC 60Hz"

### Requirement: Image dimensions and output

The rendered schematic SHALL be saved as a PNG at a minimum resolution of 800×400
pixels with a white background and black foreground, and SHALL be written to a
user-specified output path.

#### Scenario: PNG file is created at expected path

- **WHEN** a schematic is rendered with output path `/tmp/circuit.png`
- **THEN** a file exists at `/tmp/circuit.png` and is a valid PNG image at least
  800×400 pixels in size, with white background and black lines
