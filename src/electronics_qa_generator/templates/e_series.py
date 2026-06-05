"""E-series standard component values.

Provides standard value series (E6 for capacitors, E12 for resistors)
and a helper to pick a scaled value from a decade range.
"""

from __future__ import annotations

import random

E6_VALUES: list[float] = [1.0, 1.5, 2.2, 3.3, 4.7, 6.8]
"""E6 series base values (20% tolerance). Used for capacitors."""

E12_VALUES: list[float] = [
    1.0,
    1.2,
    1.5,
    1.8,
    2.2,
    2.7,
    3.3,
    3.9,
    4.7,
    5.6,
    6.8,
    8.2,
]
"""E12 series base values (10% tolerance). Used for resistors."""

# Selected inductor values (Henries) — less standardized.
INDUCTOR_VALUES: list[float] = [
    1e-3,
    2.2e-3,
    4.7e-3,
    1e-2,
    2.2e-2,
    4.7e-2,
    1e-1,
]


def pick_e_value(
    base_values: list[float],
    decade_min: int,
    decade_max: int,
    rng: random.Random,
) -> float:
    """Pick a random E-series value within a decade range.

    Args:
        base_values: The base E-series list (e.g., E12_VALUES).
        decade_min: Minimum decade exponent (e.g., 2 for 10^2 = 100).
        decade_max: Maximum decade exponent (inclusive).
        rng: Seeded random.Random instance.

    Returns:
        A value of the form base * 10^decade.

    Example:
        >>> import random
        >>> rng = random.Random(42)
        >>> v = pick_e_value(E12_VALUES, 2, 6, rng)
        >>> 100 <= v <= 8.2e6
        True
    """
    base = rng.choice(base_values)
    decade = rng.randint(decade_min, decade_max)
    return base * (10**decade)
