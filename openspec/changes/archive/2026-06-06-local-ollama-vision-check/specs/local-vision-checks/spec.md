## ADDED Requirements

### Requirement: Vision checks use local Ollama VLM

The system SHALL use the locally-running Ollama service at
`VISION_BASE_URL` (default `http://localhost:11434/v1`) with model
`VISION_MODEL` (default `deepseek-vl2-tiny`) for all visual QA checks.
No cloud API key or external service SHALL be required for vision
capabilities.

#### Scenario: Ollama service is running and model is available

- **WHEN** `eqa validate --visual` is invoked and Ollama is running
  with `deepseek-vl2-tiny` pulled
- **THEN** the system sends the schematic PNG as a base64 data URI
  to the VLM and returns the parsed WARN/PASS verdict

#### Scenario: Ollama service is not reachable

- **WHEN** `eqa validate --visual` is invoked but Ollama is not
  running or the model is not pulled
- **THEN** the vision check returns PASS with a message indicating
  the VLM was unavailable; no error is raised

### Requirement: Vision checks are advisory only

Vision check results SHALL never cause a FAIL verdict. They SHALL
only produce PASS or WARN to avoid blocking dataset assembly on
VLM availability issues.

#### Scenario: VLM reports a topology mismatch

- **WHEN** the VLM responds with `WARN: <reason>` for a
  topology-match check
- **THEN** the verdict is recorded as WARN (not FAIL) in the
  validation report

#### Scenario: VLM confirms the schematic is correct

- **WHEN** the VLM responds with `PASS` for any vision check
- **THEN** the verdict is recorded as PASS

### Requirement: Vision check configuration via environment

The system SHALL accept `VISION_BASE_URL` and `VISION_MODEL`
from environment variables or a `.env` file, overriding the
defaults (`http://localhost:11434/v1` and `deepseek-vl2-tiny`).

#### Scenario: Custom VLM endpoint configured

- **WHEN** `VISION_BASE_URL=http://gpu-server:8080/v1` is set
  in the environment
- **THEN** vision checks connect to `http://gpu-server:8080/v1`
  instead of the default

### Requirement: Vision check results are cached

The system SHALL cache vision check results keyed by image content
hash, so repeated `validate` runs on the same schematic images
do not re-invoke the VLM.

#### Scenario: Same image validated twice

- **WHEN** `eqa validate --visual` is run twice with the same
  schematic image
- **THEN** the second run reads the cached result and does not
  call the VLM
