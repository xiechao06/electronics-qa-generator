## MODIFIED Requirements

### Requirement: Template registry resolves and validates against a CircuitGraph

The system SHALL provide a registry that maps `(family, topology)` to its SVG
template file. Before rendering, the registry SHALL validate the template against
the `CircuitGraph` with **bidirectional component coverage**: (a) every declared
template slot SHALL correspond to a graph component or node, and (b) **every**
graph component (by reference designator) SHALL be represented in the template —
as a value/label slot or a visible text label. The registry SHALL raise a clear
error when a topology has no registered template, when a declared slot has no
matching component/node, or when a graph component is absent from the template.
No PNG SHALL be produced from an incomplete or inconsistent template. (Node
*labeling* requirements — that a node a question names must be visible — are
verified by the template-coverage-verification capability, since supply rails and
internal junctions are legitimately conveyed by wiring rather than text labels.)

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

- **WHEN** a template is validated against a `CircuitGraph` whose declared slots
  do not match the graph's components or nodes
- **THEN** the registry raises an error identifying the missing or extra slot
- **AND** no PNG is produced from an inconsistent template

#### Scenario: Component missing from the template is rejected

- **WHEN** a template is validated against a `CircuitGraph` that contains a
  component (e.g. a bypass capacitor or load resistor) the template does not draw
- **THEN** the registry raises an error identifying the missing component
  designator
- **AND** no PNG is produced from the incomplete template
