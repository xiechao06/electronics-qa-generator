## ADDED Requirements

### Requirement: Netlist information content is derivable per topology

The verifier SHALL derive, from a sampled `CircuitGraph`, the canonical set of
**netlist facts** that constitute the information a solver would need — namely
every component (by reference designator) and its value, every source's value,
every non-ground node, every device model name, and the analysis directive
(type and any swept/operating parameters such as frequency). This fact set is the
ground truth against which the schematic image and the question text are checked.

#### Scenario: Fact set enumerates all components and nodes

- **WHEN** the verifier is given a sampled `CircuitGraph` for a topology
- **THEN** it returns a fact set containing one entry per component designator
  (with its value), one entry per non-ground node, each device model name, and
  the analysis directive
- **AND** the fact set is derived deterministically from the graph (no LLM, no
  simulation required)

### Requirement: Schematic image must convey every netlist component and node

The verifier SHALL require that the rendered SVG schematic for a topology
represents **every** component designator and **every** non-ground node present
in the graph — as a value/label slot or a visible text label. A component or node
that exists in the netlist but is absent from the rendered schematic SHALL be
reported as a coverage failure for that topology.

#### Scenario: All components appear in the rendered schematic

- **WHEN** the verifier renders the SVG template for a topology against its
  sampled graph
- **THEN** every component designator in the graph appears in the rendered SVG
- **AND** every non-ground node appears in the rendered SVG

#### Scenario: A component missing from the schematic fails verification

- **WHEN** a graph contains a component (e.g. an emitter bypass capacitor or a
  load resistor) that the SVG template does not draw
- **THEN** the verifier reports a FAIL identifying the missing designator
- **AND** the topology is flagged as having an incomplete schematic

### Requirement: Answer-relevant facts must be visible in image or question

For each question template of a topology, the verifier SHALL determine the set of
netlist facts the answer depends on (from the template's program and declared
answer/input keys) and SHALL require that each such fact is conveyed by **either**
the rendered schematic image **or** the question text (via an inlined `{param}`
placeholder or an explicit numeric statement). A fact that the answer depends on
but that is invisible in both the image and the question SHALL be reported as an
unanswerable/ambiguous-item failure.

#### Scenario: Fact inlined in the question text satisfies coverage

- **WHEN** a question template states a component value directly in its text
  (e.g. `R1 = {R1_ohm} Ω`)
- **THEN** that fact is counted as conveyed by the question and passes coverage
  even if the schematic also shows it

#### Scenario: Fact shown only in the schematic satisfies coverage

- **WHEN** a question template references the circuit generically ("shown in the
  schematic") and the depended-on fact is drawn in the SVG
- **THEN** that fact is counted as conveyed by the image and passes coverage

#### Scenario: Hidden answer-relevant fact fails verification

- **WHEN** a question's answer depends on a netlist fact that appears in neither
  the rendered schematic nor the question text
- **THEN** the verifier reports a FAIL identifying the topology, question id, and
  the hidden fact

### Requirement: Verifier produces a per-topology report

The verifier SHALL produce a report that, for each topology, states PASS or FAIL
and enumerates every coverage failure with enough detail to locate it (the
topology, the failure kind, and the specific component, node, or question id and
fact). The report SHALL be available in a human-readable form and as JSON.

#### Scenario: Report summarizes all topologies

- **WHEN** verification runs across all registered topologies
- **THEN** the report lists each topology with a PASS/FAIL status
- **AND** every FAIL entry identifies the specific missing component, node, or
  hidden answer-relevant fact

#### Scenario: JSON output is machine-readable

- **WHEN** verification is requested with JSON output
- **THEN** the report is emitted as structured JSON suitable for CI consumption

### Requirement: Verification is exposed via CLI and regression test

The system SHALL expose the triad verifier through the `eqa` CLI so it can be run
on demand and before batch generation, and SHALL provide an automated test that
runs the verifier across all registered topologies so the triad is checked in CI.
The CLI command SHALL exit non-zero when any topology fails so it can gate
generation.

#### Scenario: CLI runs the verifier across topologies

- **WHEN** the user runs the verification subcommand
- **THEN** the verifier checks every registered topology and prints the report
- **AND** the process exits non-zero if any topology fails

#### Scenario: Regression test guards all topologies

- **WHEN** the test suite runs
- **THEN** a test invokes the verifier across all registered topologies and fails
  if any topology has a coverage failure
