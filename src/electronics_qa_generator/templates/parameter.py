"""Parameter distribution classes for constrained randomization.

Each distribution samples values deterministically given a `random.Random` instance.
Uses stdlib only — no numpy dependency.
"""

from __future__ import annotations

import math
import random
from typing import Sequence


class Uniform:
    """Uniform distribution over [min_val, max_val]."""

    def __init__(self, min_val: float, max_val: float) -> None:
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val})")
        self.min = min_val
        self.max = max_val

    def sample(self, rng: random.Random) -> float:
        return rng.uniform(self.min, self.max)


class LogUniform:
    """Log-uniform distribution over [min_val, max_val].

    Samples uniformly in log-space, yielding values spread across orders
    of magnitude.
    """

    def __init__(self, min_val: float, max_val: float) -> None:
        if min_val <= 0 or max_val <= 0:
            raise ValueError("LogUniform requires min/max > 0")
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val})")
        self._log_min = math.log10(min_val)
        self._log_max = math.log10(max_val)

    def sample(self, rng: random.Random) -> float:
        log_val = rng.uniform(self._log_min, self._log_max)
        return 10**log_val


class Choice:
    """Choose uniformly from a fixed list of values."""

    def __init__(self, values: Sequence[float]) -> None:
        if not values:
            raise ValueError("Choice requires at least one value")
        self.values = list(values)

    def sample(self, rng: random.Random) -> float:
        return rng.choice(self.values)
