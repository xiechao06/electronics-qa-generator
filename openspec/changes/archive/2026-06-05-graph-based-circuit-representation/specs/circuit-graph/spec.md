## ADDED Requirements

### Requirement: CircuitGraph construction
The system SHALL provide a `CircuitGraph` class with methods `add_resistor`, `add_capacitor`, `add_inductor`, `add_voltage_source`, and `add_diode`. Each method SHALL accept component name, positive node, negative node, and the necessary physical parameters (numeric float values, not formatted strings). Node names are strings; ground is the string `"0"`. The graph SHALL track all registered nodes and the ordered list of components.

#### Scenario: Building a voltage divider
- **WHEN** a `CircuitGraph` is created and `add_voltage_source("Vin", "in", "0", dc=5.0)`, `add_resistor("R1", "in", "out", 1000.0)`, and `add_resistor("R2", "out", "0", 2000.0)` are called
- **THEN** the graph contains 3 nodes (`"0"`, `"in"`, `"out"`) and 3 components
- **AND** the components are in insertion order

#### Scenario: Node names are case-sensitive
- **WHEN** a component references "Out" but only "out" is registered
- **THEN** `validate()` reports the mismatch

### Requirement: Graph → SPICE emission
The system SHALL provide `CircuitGraph.to_spice(simulation: SimulationConfig) -> str` that produces a valid Xyce netlist string. The output SHALL include component lines in insertion order (or a stable canonical order), the simulation control card, `.print` line(s), and `.end`. Component values SHALL be formatted with unit suffixes (k, n, m, Meg, etc.) using the same formatting rules as the current `netlist_helpers.py`.

#### Scenario: Voltage divider to_spice output is a valid Xyce netlist
- **WHEN** `to_spice(SimulationConfig(type="op"))` is called on a voltage divider graph
- **THEN** the result starts with a comment line or the first component line
- **AND** the result contains `.op`
- **AND** the result ends with `.end`

#### Scenario: AC simulation includes .ac and .print ac
- **WHEN** `to_spice(SimulationConfig(type="ac", params={"start_hz": 1, "stop_hz": 1e6, "points_per_decade": 50}))` is called
- **THEN** the result contains `.ac dec 50 1 1Meg`
- **AND** the result contains `.print ac`

#### Scenario: Transient simulation includes .tran and .print tran
- **WHEN** `to_spice(SimulationConfig(type="tran", params={"stop_s": 0.1, "step_s": 1e-5}))` is called
- **THEN** the result contains `.tran`
- **AND** the result contains `.print tran`

### Requirement: Graph validation
The system SHALL provide `CircuitGraph.validate() -> list[str]` returning an empty list for a valid circuit, or a list of error messages for problems. Checks SHALL include: all component nodes exist, no duplicate component names, at least one source, no floating nodes (exactly one connection), and ground node "0" is present.

#### Scenario: Valid circuit passes validation
- **WHEN** `validate()` is called on a correctly constructed voltage divider graph
- **THEN** the result is an empty list

#### Scenario: Floating node is reported
- **WHEN** a circuit has a node with exactly one component connected (and the node is not ground)
- **THEN** `validate()` returns a list containing a string that mentions the floating node

#### Scenario: Duplicate component names are reported
- **WHEN** two components share the same name
- **THEN** `validate()` returns a list containing a string mentioning the duplicate

#### Scenario: Unknown node reference is reported
- **WHEN** a component references a node not in `graph.nodes`
- **THEN** `validate()` returns a list containing a string mentioning the unknown node

### Requirement: Existing template output is unchanged
The five existing templates SHALL produce byte-identical `CircuitRecord.netlist` strings when ported to the graph API. Node names, component ordering, comment lines, value formatting, simulation cards, and `.end` placement SHALL match exactly.

#### Scenario: VoltageDivider netlist is byte-identical
- **WHEN** `VoltageDivider().sample(seed=42)` is called after the port
- **THEN** `record.netlist` equals the netlist produced by the current string-based implementation for the same seed

#### Scenario: RCBandPass netlist is byte-identical
- **WHEN** `RLCBandPass().sample(seed=7)` is called after the port
- **THEN** `record.netlist` equals the current string-based output for the same seed

### Requirement: Graph query methods
The system SHALL provide `CircuitGraph` methods for topology inspection: `node_count` (int property), `component_count` (int property), `nodes` (set[str] property, excluding ground), and `components_by_kind(kind: str) -> list[Component]`.

#### Scenario: Node and component counts are correct
- **WHEN** a voltage divider graph has 3 components and 2 non-ground nodes
- **THEN** `graph.component_count == 3`
- **AND** `graph.node_count == 2`
- **AND** `graph.nodes == {"in", "out"}`

#### Scenario: Components by kind filters correctly
- **WHEN** `components_by_kind("resistor")` is called on a mixed circuit
- **THEN** only resistor components are returned
