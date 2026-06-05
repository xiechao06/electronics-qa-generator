## ADDED Requirements

### Requirement: Question template registry
The system SHALL provide a `QUESTION_TEMPLATES` dict mapping topology name to a list of question template dicts. Each template dict SHALL contain keys `id`, `question_type`, `question_template`, `program`, `answer_keys`, and `answer_formatter`.

#### Scenario: All topologies have templates
- **WHEN** the system is loaded
- **THEN** `QUESTION_TEMPLATES` contains keys for `"voltage_divider"`, `"rc_lowpass"`, `"rc_highpass"`, `"rlc_bandpass"`, and `"half_wave_rectifier"`
- **AND** each topology has at least 2 question templates

### Requirement: Question template types
Each question template SHALL have a `question_type` field with one of: `"direct"`, `"derived"`, `"classification"`, or `"comparison"`.

#### Scenario: Direct questions read a fact
- **WHEN** a template has `question_type: "direct"`
- **THEN** the program contains a `read_fact` op targeting a key in the fact dict
- **AND** the answer formatter is `"numeric"`

#### Scenario: Classification questions pick a label
- **WHEN** a template has `question_type: "classification"`
- **THEN** the program contains a `classify` op with a `labels` array
- **AND** the `choices` field in the generated `QAItem` is populated with those labels

### Requirement: CLEVR-style program representation
Each question template SHALL include a `program` field that is an ordered list of dicts. Each dict SHALL have an `op` field with one of: `read_fact`, `read_param`, `add`, `sub`, `mul`, `div`, `abs`, `compare`, `classify`, `format_numeric`, `return_bool`, `return_label`. Ops that reference previous results SHALL use `$N` notation where N is the 0-based result index.

#### Scenario: Program is deterministic
- **WHEN** the same facts and params are provided to `compute_answer` twice with the same program
- **THEN** the same `(answer_value, answer_text, unit, tolerance)` is returned

### Requirement: Deterministic answer computation
The system SHALL provide `compute_answer(program: list[dict], facts: dict, params: dict) -> tuple` that evaluates the program ops in order and returns `(answer_value: float | None, answer_text: str, unit: str | None, tolerance: float | None)`.

#### Scenario: Direct numeric answer
- **WHEN** the program reads `Vout_dc` from facts containing `{"Vout_dc": 3.14}`
- **THEN** `answer_value` is 3.14 and `answer_text` is `"3.14 V"`
- **AND** `unit` is `"V"` and `tolerance` is derived from precision

#### Scenario: Classification answer
- **WHEN** the program classifies `behavior` as `"low-pass"`
- **THEN** `answer_text` is `"low-pass"` and `answer_value` is None
- **AND** `unit` and `tolerance` are None

### Requirement: Question generation from facts
The system SHALL provide `generate_questions(topology: str, facts: dict, params: dict) -> list[QAItem]` that instantiates all question templates for the given topology, computes answers, and returns populated `QAItem` records.

#### Scenario: Each generated QAItem has required fields
- **WHEN** `generate_questions` is called for a valid topology
- **THEN** each returned `QAItem` has non-empty `question_type`, `question`, `answer`, and `program` fields

#### Scenario: Unknown topology raises an error
- **WHEN** `generate_questions` is called with an unknown topology
- **THEN** a `KeyError` is raised with a message naming the topology
