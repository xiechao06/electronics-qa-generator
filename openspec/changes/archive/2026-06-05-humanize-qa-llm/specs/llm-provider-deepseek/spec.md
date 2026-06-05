## ADDED Requirements

### Requirement: DeepSeek chat-completions client

The system SHALL provide a client that calls the DeepSeek chat-completions API using
the `deepseek-v4-pro` model by default, sending a system and user message and returning
the assistant's text content. The client SHALL use only the Python standard library for
HTTP transport so that no new required dependency is introduced.

#### Scenario: Successful completion

- **WHEN** the client is invoked with valid configuration and the API responds with a
  chat completion
- **THEN** the client returns the assistant message content as a string

#### Scenario: Standard-library transport

- **WHEN** the client issues an HTTP request
- **THEN** it uses the Python standard library (e.g., `urllib.request`) and `json`,
  without importing any third-party HTTP package

### Requirement: Configuration via .env file

The client SHALL read its API key from a `.env` file (`DEEPSEEK_API_KEY`) in the
project root (falling back to the current working directory) and SHALL allow the base
URL and model name to be overridden via the same `.env` file keys (`DEEPSEEK_BASE_URL`,
`DEEPSEEK_MODEL`), defaulting to the DeepSeek endpoint and `deepseek-v4-pro` when
overrides are absent. The `.env` file SHALL be parsed using only the Python standard
library (no `python-dotenv` dependency).

#### Scenario: Defaults applied

- **WHEN** a `.env` file contains only `DEEPSEEK_API_KEY`
- **THEN** the client targets the default DeepSeek base URL and the `deepseek-v4-pro`
  model

#### Scenario: Overrides honored

- **WHEN** the `.env` file also sets `DEEPSEEK_BASE_URL` and/or `DEEPSEEK_MODEL`
- **THEN** the client uses the overridden base URL and/or model

#### Scenario: Missing key reports unavailability

- **WHEN** no `.env` file exists or it lacks `DEEPSEEK_API_KEY`
- **THEN** the client reports that it is unavailable (rather than attempting a call),
  so callers can fall back to pass-through behavior

### Requirement: Bounded timeouts and error handling

The client SHALL apply a request timeout and SHALL surface failures (network errors,
non-2xx responses, malformed JSON) as a single well-defined exception type that callers
can catch.

#### Scenario: Request times out

- **WHEN** the API does not respond within the configured timeout
- **THEN** the client raises the client's defined error type

#### Scenario: Non-success HTTP status

- **WHEN** the API returns a non-2xx status code
- **THEN** the client raises the client's defined error type with the status available
  for diagnostics
