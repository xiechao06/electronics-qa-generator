## ADDED Requirements

### Requirement: MMMU-compatible JSONL output

The assembler SHALL produce a `.jsonl` file where each line is a JSON object with
fields: `id`, `question`, `answer`, `options` (JSON string or null), `explanation`,
and `image` (relative path to the schematic PNG).

#### Scenario: Direct question

- **WHEN** a "direct" QA item with answer "233.496 Hz" is assembled
- **THEN** the JSONL line has `"answer": "233.496 Hz"` and `"options": null`

#### Scenario: Classification question

- **WHEN** a classification item with choices ["low-pass", "high-pass", "band-pass"]
  and answer "low-pass" is assembled
- **THEN** the JSONL line has `"options": "['low-pass', 'high-pass', 'band-pass']"`
  and `"answer": "low-pass"`

### Requirement: Self-contained output directory

The assembler SHALL produce a single output directory containing `dataset.jsonl`,
all schematic PNGs under `images/`, and a `report.json` validation summary. Image
paths in the JSONL SHALL be relative to the output root (e.g., `"images/rc_lowpass_0000002a.png"`).

#### Scenario: Output directory structure

- **WHEN** `eqa assemble --out my_dataset` runs
- **THEN** `my_dataset/dataset.jsonl` and `my_dataset/images/*.png` exist

### Requirement: Render always on for questions

The `eqa questions` command SHALL always render schematic images alongside generated
QA items. The `--render` flag SHALL be accepted as a no-op for backwards compatibility.

#### Scenario: Questions always include schematic_path

- **WHEN** `eqa questions voltage_divider` runs
- **THEN** each emitted item has a non-null `schematic_path` field pointing to the
  rendered PNG
