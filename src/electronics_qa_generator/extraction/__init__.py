"""Fact extractor: build the canonical ground-truth fact table.

Derives canonical facts from parsed outputs: DC output voltage, gain at a
frequency, -3 dB cutoff, phase at cutoff, peak-to-peak ripple, rise/settling
time, clipping, and behavior classification (low/high/band-pass). This fact
table is the single source of truth for answers.
"""

from .parsers import parse_ac, parse_op, parse_tran
from .facts import FACT_EXTRACTORS, find_cutoff_frequency
from .scoring import RichnessScore, compute_richness

__all__ = [
    "parse_op",
    "parse_ac",
    "parse_tran",
    "FACT_EXTRACTORS",
    "find_cutoff_frequency",
    "RichnessScore",
    "compute_richness",
]
