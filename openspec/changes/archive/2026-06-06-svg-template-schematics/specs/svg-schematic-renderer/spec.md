## ADDED Requirements

### Requirement: Fill SVG template with sampled circuit data

The system SHALL accept a `CircuitGraph` and its resolved SVG template, fill every
value/label slot with the sampled circuit's reference designators and formatted
component values, and fill node-label slots with the graph's node names. Filling
SHALL reuse the existing engineering-unit formatting so labels match the rest of the
pipeline (e.g., `R1 4.7k Ω`, `C1 100n F`, `V1 5V DC`).

#### Scenario: Component values populate their slots

- **WHEN** a voltage-divider `CircuitGraph` (R1, R2, Vin) is filled into its template
- **THEN** the `R1`, `R2`, and `Vin` slots display their formatted value+unit labels
- **AND** node-label slots display the graph's node names (e.g., `in`, `out`)

#### Scenario: Filling does not alter ground truth

- **WHEN** a graph is filled into its template
- **THEN** only presentation slots (symbols, labels, node names) are populated
- **AND** the netlist, simulation config, and probes are unchanged

### Requirement: Rasterize filled template to deterministic PNG

The system SHALL rasterize the filled SVG to a PNG written to a caller-specified
output path. For a given `CircuitGraph` and template, repeated renders SHALL produce
pixel-identical PNGs (deterministic output), with white background and black
foreground.

#### Scenario: PNG is produced at the requested path

- **WHEN** a filled template is rendered with output path `/tmp/circuit.png`
- **THEN** a valid PNG file exists at `/tmp/circuit.png`

#### Scenario: Two renders are identical

- **WHEN** the same `CircuitGraph` is rendered twice through the SVG renderer
- **THEN** the two PNG files are pixel-identical

### Requirement: Schematic renderer dispatches to the SVG path when available

The schematic renderer SHALL render via the SVG template path when the topology has
a registered template, and SHALL otherwise preserve the existing rendering behavior.
The public render entry point SHALL keep its current signature so callers and the
render CLI need no changes.

#### Scenario: Registered topology uses the SVG renderer

- **WHEN** `render_schematic` is called for a topology with a registered SVG template
- **THEN** the output PNG is produced from the filled SVG template

#### Scenario: Unregistered topology falls back

- **WHEN** `render_schematic` is called for a topology without a registered SVG template
- **THEN** the renderer falls back to the existing matplotlib layout and still
  produces a PNG at the requested path
