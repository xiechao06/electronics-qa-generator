"""Sample richness scoring.

Computes a quality score for each simulated sample. The score indicates
whether the sample is interesting enough to keep for the dataset.
Initial implementation uses neutral defaults; the scoring model is
extensible for comparison-based separability scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RichnessScore:
    """Quality score for a simulated sample (0.0 – 1.0)."""

    total: float = 0.5
    separability: float = 0.5
    stability: float = 0.5
    probe_coverage: float = 1.0


def compute_richness(
    facts: dict[str, Any],
    sim_result: Any,  # SimResult — imported lazily to avoid circular deps
    all_samples: list[dict] | None = None,
) -> RichnessScore:
    """Compute a richness score for a simulated sample.

    Args:
        facts: Extracted fact dict from the simulation.
        sim_result: The SimResult from running Xyce.
        all_samples: Optional list of all sample fact dicts for
            comparison-based separability scoring (future use).

    Returns:
        RichnessScore with fields in [0.0, 1.0].
    """
    if not sim_result.success or not sim_result.converged:
        return RichnessScore(
            total=0.0,
            separability=0.0,
            stability=0.0,
            probe_coverage=0.0,
        )

    # Neutral defaults for now — will be enriched when comparison data
    # is available from batch simulation runs.
    _ = all_samples  # reserved for future use

    return RichnessScore(
        total=0.5,
        separability=0.5,
        stability=0.5,
        probe_coverage=1.0,
    )
