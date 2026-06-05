## ADDED Requirements

### Requirement: Invoke Xyce from a netlist
The system SHALL provide `invoke_xyce(netlist: str, timeout_s: int = 30) -> tuple[str, int, bool]` that writes the netlist to a temporary `.cir` file, runs `xyce <file>`, and returns `(stdout, returncode, converged)`. If Xyce is not on PATH, SHALL raise `RuntimeError`.

#### Scenario: Successful Xyce run
- **WHEN** `invoke_xyce` is called with a valid voltage divider netlist
- **THEN** returncode is 0 and `converged` is True
- **AND** stdout contains simulation output

#### Scenario: Xyce not on PATH
- **WHEN** `invoke_xyce` is called and `xyce` is not found
- **THEN** a `RuntimeError` with a helpful message is raised

### Requirement: Retry with perturbation on failure
The system SHALL provide `run_xyce_with_retry(graph: CircuitGraph, simulation: SimulationConfig, max_attempts: int = 3, timeout_s: int = 30) -> SimResult`. On netlist convergence failure, the graph SHALL be perturbed (±5% on resistor values), re-emitted, and retried. After `max_attempts` failures, a failed `SimResult` SHALL be returned.

#### Scenario: First attempt succeeds
- **WHEN** `run_xyce_with_retry` is called and Xyce succeeds on the first try
- **THEN** `SimResult.success` is True and `SimResult.converged` is True

#### Scenario: Retry after convergence failure
- **WHEN** Xyce fails to converge on the first netlist but converges after resistor perturbation
- **THEN** `SimResult.success` is True

#### Scenario: All attempts fail
- **WHEN** Xyce fails to converge after `max_attempts` perturbations
- **THEN** `SimResult.success` is False and an error message is recorded

### Requirement: SimResult data class
The system SHALL define a `SimResult` dataclass with fields `success` (bool), `sim_type` (str), `raw_output` (str), `exit_code` (int), `error_message` (str | None), and `converged` (bool).

### Requirement: Timeout enforcement
Xyce invocations SHALL respect a `timeout_s` parameter. If Xyce exceeds the timeout, the process SHALL be killed and `SimResult.success` SHALL be False with an appropriate error message.

#### Scenario: Timeout kills process
- **WHEN** a netlist causes Xyce to run longer than `timeout_s` seconds
- **THEN** the subprocess is killed and `SimResult.success` is False
