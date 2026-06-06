## ADDED Requirements

### Requirement: Prompt files group questions by schematic image

The system SHALL emit, during batch generation, one prompt markdown file per
(schematic image, seed) pair. Each prompt file SHALL reference the schematic
image by its filesystem path and SHALL list every Q/A item associated with that
image as numbered questions, omitting ground-truth answers.

#### Scenario: Prompt file includes image reference and numbered questions

- **WHEN** batch generation produces QA items for a topology at a given seed
- **THEN** a prompt file named `<topology>_<seed>.md` is written under `prompts/`
- **AND** the file begins with the image path, e.g. `![schematic](../images/<topology>/<seed>.png)`
- **AND** every question for that image is listed as `N. <question text>`, numbered sequentially from 1

#### Scenario: Prompt file omits answers and netlist

- **WHEN** a prompt file is written
- **THEN** it does NOT contain `answer`, `answer_value`, `netlist`, `program`,
  or any other field that would reveal the ground truth

### Requirement: Answer files mirror prompt files with ground-truth answers

The system SHALL emit, alongside each prompt file, a corresponding answer file
containing the same numbered questions and their ground-truth answers. The answer
file SHALL use the convention `<topology>_<seed>_answers.md`.

#### Scenario: Answer file pairs each question with its correct answer

- **WHEN** a prompt file lists *N* questions
- **THEN** the answer file contains entries `N. <answer>` matching the same numbering
- **AND** each entry includes the answer value, unit, and tolerance when applicable

#### Scenario: Answer and prompt directories are co-located

- **WHEN** answer files are generated
- **THEN** they reside in the same `prompts/` directory as the corresponding
  prompt files, so a human or script can diff them side-by-side

### Requirement: Prompt generation is optional and non-disruptive

The system SHALL generate prompt and answer files only when an explicit flag is
passed to the batch generation script. When the flag is absent, existing
behaviour SHALL be unchanged.

#### Scenario: Default batch generation does not produce prompt files

- **WHEN** `scripts/batch_generate.py` is run without `--prompts`
- **THEN** no `prompts/` directory is created
- **AND** the pipeline output is identical to the current behaviour

#### Scenario: Prompt flag produces prompt and answer files

- **WHEN** `scripts/batch_generate.py` is run with `--prompts`
- **THEN** a `prompts/` directory is created under the output directory
- **AND** it contains one prompt `.md` and one answer `.md` per (topology, seed) pair
