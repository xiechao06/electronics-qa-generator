"""Base class for circuit templates.

Defines the CircuitTemplate abstract base class that all circuit families
must implement, along with the template hierarchy.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod

from ..models import CircuitRecord


class CircuitTemplate(ABC):
    """Abstract base class for all circuit templates.

    Subclasses must set `family` and `topology` class attributes
    and implement `sample(seed)` returning a CircuitRecord.
    """

    family: str
    topology: str

    @abstractmethod
    def sample(self, seed: int | None = None) -> CircuitRecord:
        """Sample one circuit instance from this template.

        Args:
            seed: Optional seed for reproducibility. If None, uses system entropy.

        Returns:
            A fully populated CircuitRecord with id, family, topology,
            parameters, netlist, simulation config, and probes.
        """
        ...

    def _new_rng(self, seed: int | None) -> random.Random:
        return random.Random(seed)
