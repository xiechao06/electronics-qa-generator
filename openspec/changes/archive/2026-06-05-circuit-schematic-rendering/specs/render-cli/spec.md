## ADDED Requirements

### Requirement: Opt-in render flag on emit and questions commands

The `eqa emit` and `eqa questions` commands SHALL accept a `--render` flag that, when
set, produces a schematic PNG image for each circuit and includes the image path in
their output. When the flag is absent, the commands SHALL behave exactly as before.

#### Scenario: emit without render flag preserves current behavior

- **WHEN** `eqa emit voltage_divider` is run without `--render`
- **THEN** only the netlist and JSON record are emitted; no PNG file is created

#### Scenario: emit with render flag produces schematic PNG

- **WHEN** `eqa emit voltage_divider --render` is run
- **THEN** a `.png` schematic file is produced alongside the JSON output
- **AND** the JSON output includes a `schematic_path` field pointing to the PNG

#### Scenario: questions without render flag preserves current behavior

- **WHEN** `eqa questions voltage_divider` is run without `--render`
- **THEN** QA items are emitted as JSON; no image rendering occurs

#### Scenario: questions with render flag includes schematic path

- **WHEN** `eqa questions voltage_divider --render` is run
- **THEN** each emitted QA item includes a `schematic_path` field pointing to its
  rendered schematic PNG

### Requirement: Output directory for rendered images

When `--render` is set, generated image files SHALL be placed in an output directory
(default: `out/render/` or the directory specified by `--out`), and paths in the JSON
output SHALL be relative to the output root.

#### Scenario: Default output directory

- **WHEN** `eqa emit voltage_divider --render` runs without `--out`
- **THEN** the schematic PNG is placed under an `out/render/` directory (created if
  needed)

#### Scenario: Custom output directory

- **WHEN** `eqa emit voltage_divider --render --out my_output` runs
- **THEN** the schematic PNG is placed under `my_output/render/` (created if needed)

### Requirement: Render failures do not break the command

When `--render` is set but rendering fails (e.g., missing `matplotlib`, disk full,
layout error), the command SHALL emit items without a `schematic_path` field and SHALL
exit successfully, logging the failure.

#### Scenario: Missing matplotlib

- **WHEN** `eqa emit --render` runs but matplotlib is not installed
- **THEN** a warning is logged and items are emitted without `schematic_path`
