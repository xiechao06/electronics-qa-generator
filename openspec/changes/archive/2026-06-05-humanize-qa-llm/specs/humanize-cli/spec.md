## ADDED Requirements

### Requirement: Opt-in humanization flag on the questions command

The `eqa questions` command SHALL accept a `--humanize` flag that, when set, routes each
generated `QAItem` through the LLM humanization stage before output. When the flag is
absent, the command SHALL behave exactly as before (no network calls, identical
output).

#### Scenario: Flag omitted preserves current behavior

- **WHEN** `eqa questions <topology>` is run without `--humanize`
- **THEN** items are emitted with their original templated question text and no provider
  call is made

#### Scenario: Flag enables humanization

- **WHEN** `eqa questions <topology> --humanize` is run
- **THEN** each emitted item's question reflects the humanization stage output while its
  answer fields remain unchanged

### Requirement: Emit reworded question and explanation in output

When humanization is enabled, the command SHALL include the (possibly reworded)
`question` and the optional `explanation` in its JSON and JSONL output, alongside the
unchanged `answer`, `answer_value`, `unit`, `tolerance`, `choices`, and `program`
fields.

#### Scenario: Explanation field present in output

- **WHEN** humanization produces an explanation and the command emits an item
- **THEN** the output object includes an `explanation` field with the generated text

#### Scenario: Answer fields unchanged in output

- **WHEN** the command emits a humanized item
- **THEN** the `answer`, `answer_value`, `unit`, `tolerance`, `choices`, and `program`
  fields equal those that would be emitted without `--humanize`

### Requirement: Humanization failures do not break the command

When `--humanize` is set but the provider is unavailable or fails, the command SHALL
emit the original items unchanged and SHALL exit successfully.

#### Scenario: Provider unavailable during humanize run

- **WHEN** `eqa questions <topology> --humanize` runs with no API key configured
- **THEN** the command emits the original templated items and exits with status 0
