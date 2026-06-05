## ADDED Requirements

### Requirement: Per-topology SVG layout templates

The system SHALL provide a hand-authored SVG layout template for each supported
circuit topology. Each template SHALL be topology-correct — every wire visually
connects to the exact component terminals and nodes implied by the topology — and
SHALL contain named placeholder slots for component symbols, component value/label
text, and node labels. Templates SHALL be authored per topology (not per sampled
instance) so that one template serves every parameter sampling of that topology.

#### Scenario: MVP topologies each have a template

- **WHEN** the registry is queried for any of the 5 MVP topologies (voltage divider,
  RC low-pass, RC high-pass, RLC band-pass, half-wave rectifier)
- **THEN** a corresponding SVG template file is resolved for that `(family, topology)`

#### Scenario: Template slots are named and discoverable

- **WHEN** an SVG template is loaded
- **THEN** each placeholder slot is identified by a stable name (e.g., a value slot
  keyed by reference designator like `R1`, and node-label slots keyed by node name)
- **AND** the set of slot names can be enumerated programmatically

### Requirement: Template registry resolves and validates against a CircuitGraph

The system SHALL provide a registry that maps `(family, topology)` to its SVG
template file. Before rendering, the registry SHALL validate that the template's
slots correspond to the `CircuitGraph`'s components and nodes, and SHALL raise a
clear error when a topology has no registered template or when slots do not match
the graph.

#### Scenario: Registry resolves a known topology

- **WHEN** a `CircuitGraph` with family `passive` and topology `voltage_divider`
  is passed to the registry
- **THEN** the registry returns the resolved SVG template for that topology

#### Scenario: Unknown topology reports missing template

- **WHEN** a `CircuitGraph` whose topology has no registered SVG template is passed
  to the registry
- **THEN** the registry signals that no template is registered (so the caller can
  fall back or fail explicitly)

#### Scenario: Slot/graph mismatch is rejected

- **WHEN** a template is validated against a `CircuitGraph` whose components or nodes
  do not match the template's declared slots
- **THEN** the registry raises an error identifying the missing or extra slot
- **AND** no PNG is produced from an inconsistent template
