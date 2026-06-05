## ADDED Requirements

### Requirement: Schematic images organized by topology

The system SHALL write all rendered schematic PNGs into a per-topology
subdirectory under the images output directory. The path format SHALL be
`<output>/images/<topology>/<seed_hex>.png` where `<topology>` is the
circuit topology name (e.g., `voltage_divider`, `rc_lowpass`) and
`<seed_hex>` is the zero-padded hexadecimal representation of the
sample seed.

#### Scenario: Batch generation writes per-topology images

- **WHEN** batch generation runs with 14 topologies and output directory `output/batch`
- **THEN** images exist at `output/batch/images/voltage_divider/00000001.png` through `output/batch/images/rlc_series_resonance/000003e8.png`
- **AND** no images exist directly in `output/batch/images/`

#### Scenario: Emit command writes per-topology image

- **WHEN** `eqa emit voltage_divider --seed 42 --render -o output/single`
- **THEN** the schematic PNG exists at `output/single/images/voltage_divider/0000002a.png`

#### Scenario: Questions command writes per-topology image

- **WHEN** `eqa questions voltage_divider --seed 42 -o output/single`
- **THEN** the rendered schematic exists at `output/single/images/voltage_divider/0000002a.png`

### Requirement: Schematic paths in QA items reflect topology subdirectories

The `schematic_path` field in every generated `QAItem` SHALL use the
per-topology path format `<output_prefix>/images/<topology>/<seed_hex>.png`,
so that consumers can locate the image relative to the dataset root.

#### Scenario: QA item references image in topology subdirectory

- **WHEN** a QA item is generated for topology `rc_lowpass` with seed 42
- **THEN** the `schematic_path` field is `images/rc_lowpass/0000002a.png`

#### Scenario: All QA items in a batch use per-topology paths

- **WHEN** batch generation completes for 1,588 seeds across 14 topologies
- **THEN** every QA item's `schematic_path` references an image in a
  topology-named subdirectory
- **AND** no `schematic_path` contains a flat `images/<name>_<seed>.png` pattern

### Requirement: Assembler preserves per-topology image structure

The dataset assembler SHALL copy schematic images while preserving the
per-topology subdirectory structure. When assembling a dataset, images
from `images/<topology>/` SHALL be copied to the dataset's
`images/<topology>/` directory.

#### Scenario: Assembler copies topology subdirectories

- **WHEN** the assembler processes QA items referencing 14 topologies
- **THEN** the dataset output contains 14 subdirectories under `dataset/images/`
- **AND** each subdirectory contains all schematic PNGs for that topology
