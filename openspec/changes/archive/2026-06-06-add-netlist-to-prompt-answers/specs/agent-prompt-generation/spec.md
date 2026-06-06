## MODIFIED Requirements

### Requirement: Answer files mirror prompt files with ground-truth answers

The system SHALL emit, alongside each prompt file, a corresponding answer file
containing the same numbered questions and their ground-truth answers. The answer
file SHALL use the convention `<topology>_<seed>_answers.md`. After the numbered
answers, the answer file SHALL include a `## Netlist` section containing the
SPICE netlist for the schematic, so the operator can cross-reference the circuit
topology while verifying answers.

#### Scenario: Answer file pairs each question with its correct answer

- **WHEN** a prompt file lists *N* questions
- **THEN** the answer file contains entries `N. <answer>` matching the same numbering
- **AND** each entry includes the answer value, unit, and tolerance when applicable

#### Scenario: Answer file includes the SPICE netlist

- **WHEN** an answer file is generated for a (topology, seed) pair
- **THEN** the file ends with a `## Netlist` section containing the SPICE netlist
  block associated with that schematic

#### Scenario: Answer and prompt directories are co-located

- **WHEN** answer files are generated
- **THEN** they reside in the same `prompts/` directory as the corresponding
  prompt files, so a human or script can diff them side-by-side
