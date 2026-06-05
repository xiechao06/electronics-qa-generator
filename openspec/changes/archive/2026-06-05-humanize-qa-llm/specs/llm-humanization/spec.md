## ADDED Requirements

### Requirement: Reword finalized questions without altering ground truth

The system SHALL provide a humanization function that accepts a finalized `QAItem`
(one whose answer has already been computed deterministically) and returns a new
`QAItem` whose `question` text is reworded into natural, exam-style language while
the `answer`, `answer_value`, `unit`, `tolerance`, `choices`, and `program` fields
remain byte-for-byte identical to the input.

#### Scenario: Question is reworded, answer preserved

- **WHEN** a finalized `QAItem` is passed to the humanization function with a working
  LLM provider that returns a paraphrase
- **THEN** the returned item's `question` differs from (or may equal) the input text
- **AND** the returned item's `answer`, `answer_value`, `unit`, `tolerance`, `choices`,
  and `program` are exactly equal to the input item's corresponding fields

#### Scenario: Provider output that changes any answer field is rejected

- **WHEN** the LLM provider returns content that, if applied, would change any
  deterministic answer field
- **THEN** the humanization function discards the LLM output and returns an item with
  the original deterministic fields intact (keeping the original question text)

### Requirement: Generate an optional explanation

The system SHALL optionally populate the `QAItem.explanation` field with an
LLM-generated natural-language explanation that references only the already-computed
answer and stated facts, and SHALL never use the explanation to introduce a new or
different numeric answer.

#### Scenario: Explanation is attached

- **WHEN** humanization runs with explanation generation enabled and the provider
  returns explanation text
- **THEN** the returned `QAItem.explanation` is set to that text
- **AND** all deterministic answer fields remain unchanged

#### Scenario: Explanation disabled or unavailable

- **WHEN** explanation generation is disabled, or the provider returns no explanation
- **THEN** `QAItem.explanation` is left as `None` and the item is otherwise unchanged

### Requirement: Offline-safe pass-through fallback

The humanization function SHALL never raise on missing configuration or provider
failure; when no API key is configured or the provider call fails, it SHALL return the
input item unchanged.

#### Scenario: No API key configured

- **WHEN** humanization is requested but no `.env` file with a DeepSeek API key is
  found
- **THEN** the function returns the input `QAItem` unchanged without making a network
  call

#### Scenario: Provider call raises or times out

- **WHEN** the provider raises an exception, times out, or returns malformed output
- **THEN** the function returns the input `QAItem` unchanged and does not propagate the
  error

### Requirement: Cache humanized results

The system SHALL cache humanization results keyed by the original question text, the
target model name, and a humanization options signature, so that repeated requests for
the same input return the cached reworded output without a new provider call.

#### Scenario: Cache hit avoids a provider call

- **WHEN** the same finalized question is humanized twice with the same model and
  options and caching is enabled
- **THEN** the second call returns the cached result and does not invoke the provider
