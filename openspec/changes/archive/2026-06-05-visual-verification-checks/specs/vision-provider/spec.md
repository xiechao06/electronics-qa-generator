## ADDED Requirements

### Requirement: Vision model chat completions

The system SHALL provide a `complete_vision()` function that sends a base64-encoded
PNG image along with a text prompt to a VLM endpoint via the OpenAI-compatible
`/v1/chat/completions` API. The function SHALL use the existing stdlib `urllib`
transport pattern.

#### Scenario: Successful vision completion

- **WHEN** `complete_vision("system prompt", "user prompt", "/path/to/schematic.png")`
  is called with a running Ollama instance
- **THEN** the function returns the VLM's text response

#### Scenario: VLM unavailable returns empty

- **WHEN** the VLM endpoint is unreachable
- **THEN** the function returns an empty string rather than raising

### Requirement: Schematic–topology match check

The system SHALL send the rendered schematic PNG and the topology name to the VLM
with a prompt asking whether the schematic matches the stated topology. A mismatch
SHALL return WARN.

#### Scenario: Matching schematic passes

- **WHEN** an RC low-pass schematic is checked against topology "rc_lowpass"
- **THEN** the VLM confirms the match and the check returns PASS

#### Scenario: Mismatched schematic warns

- **WHEN** a voltage divider schematic is checked against topology "rc_lowpass"
- **THEN** the VLM detects the mismatch and the check returns WARN

### Requirement: Label visibility check

The system SHALL send the rendered schematic PNG to the VLM with a prompt asking
whether all component labels are clearly readable. If labels are obscured, clipped,
or too small, the check SHALL return WARN.

#### Scenario: Readable labels pass

- **WHEN** a well-rendered schematic with clear "R1 4.7k Ω" labels is checked
- **THEN** the check returns PASS

#### Scenario: Illegible labels warn

- **WHEN** a schematic with overlapping or clipped labels is checked
- **THEN** the check returns WARN with details about the visibility issue
