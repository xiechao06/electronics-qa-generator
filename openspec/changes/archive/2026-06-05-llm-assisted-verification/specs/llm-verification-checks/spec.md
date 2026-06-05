## ADDED Requirements

### Requirement: Wording ambiguity check

The system SHALL use an LLM to assess whether a QA item's question text contains
ambiguous phrasing that could confuse a human solver or model. The check SHALL
return WARN when ambiguity is detected and PASS otherwise. When the LLM provider
is unavailable, the check SHALL return PASS (not FAIL).

#### Scenario: Clear question passes

- **WHEN** the question "Find the −3 dB cutoff frequency of this RC low-pass filter."
  is sent to the LLM
- **THEN** the check returns PASS

#### Scenario: Ambiguous question warns

- **WHEN** the question "What is the voltage at the output?" is sent to the LLM
  without specifying which output node in a multi-output circuit
- **THEN** the check returns WARN with an explanation of the ambiguity

#### Scenario: Provider unavailable passes through

- **WHEN** the DeepSeek API key is not configured
- **THEN** the check returns PASS without making a network call

### Requirement: Semantic leakage check

The system SHALL use an LLM to detect whether a question text implicitly reveals
its own answer through phrasing (e.g., "Given the cutoff is 233 Hz, find the
bandwidth"). Detected leakage SHALL return WARN.

#### Scenario: No leakage passes

- **WHEN** the question "Find the cutoff frequency of the filter shown." is sent
  to the LLM
- **THEN** the check returns PASS

#### Scenario: Leaked answer warns

- **WHEN** the question "Given the −3 dB cutoff is 233 Hz, calculate the required
  capacitor value." is sent to the LLM
- **THEN** the check returns WARN indicating the answer is embedded in the premise

### Requirement: Difficulty scoring

The system SHALL use an LLM to assign a difficulty label of "easy", "medium", or
"hard" to each QA item based on the question's cognitive complexity. The score
SHALL be stored in the CheckResult message, and the verdict SHALL always be PASS
(scoring is informational, not a quality gate).

#### Scenario: Recall question scores easy

- **WHEN** a question asking for a directly simulated value is scored
- **THEN** the LLM returns a difficulty label of "easy" or "medium"

#### Scenario: Multi-step derivation scores higher

- **WHEN** a question requiring formula derivation and unit conversion is scored
- **THEN** the LLM returns a difficulty label of "medium" or "hard"

### Requirement: Caching of LLM responses

LLM check results SHALL be cached by question text hash so repeated runs on the
same item do not incur additional API calls.

#### Scenario: Cache hit avoids call

- **WHEN** the same question is checked twice with LLM verification enabled
- **THEN** the second invocation returns the cached result without calling the provider

### Requirement: Check function interface

Each LLM check SHALL follow the same `(item, *, provider) -> CheckResult` signature
as static checks and SHALL integrate into the existing `ValidationReport` pipeline
without requiring changes to the report model.

#### Scenario: Integration with ValidationReport

- **WHEN** `ValidationReport.from_items()` is called with LLM checks enabled
- **THEN** LLM check results appear alongside static check results in the report
