"""Simulation orchestrator + Xyce runner.

Responsible for batching, parallel workers, retries, timeouts, caching of
duplicate simulations, and recording failures. Runs Xyce for .op/.dc/.ac/.tran
analyses. The simulator owns the truth.
"""

from .models import SimResult
from .cache import FactCache

__all__ = ["SimResult", "FactCache"]
