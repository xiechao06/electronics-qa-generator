"""Simulation data models.

Lightweight dataclasses for Xyce simulation results.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimResult:
    """Result of a Xyce simulation run.

    Fields:
        success: True if simulation completed without subprocess errors.
        sim_type: Simulation type string ("op", "ac", "tran", "dc").
        raw_output: Captured stdout from Xyce.
        exit_code: Process exit code.
        error_message: Stderr text or None if no error.
        converged: True if Xyce reported numerical convergence.
    """

    success: bool
    sim_type: str
    raw_output: str
    exit_code: int
    error_message: str | None = None
    converged: bool = False
