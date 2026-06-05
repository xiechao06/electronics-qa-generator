"""Xyce output parsers.

Parse Xyce .print op / .print ac / .print tran text output into structured
Python data. All parsers are pure functions that accept raw stdout text and
return typed dicts.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_SPLIT_RE = re.compile(r"\s+")


def _float_or_none(s: str) -> float | None:
    """Parse a string to float, return None on failure."""
    try:
        return float(s)
    except ValueError, TypeError:
        return None


def _parse_table(lines: list[str]) -> tuple[list[str], list[list[float]]]:
    """Parse Xyce table output into (column_headers, data_rows).

    Xyce format:
        Column1  Column2  Column3
        ------   ------   ------
        0.000    1.234    5.678
        ...

    Returns:
        column_headers: list of header names (stripped)
        data_rows: list of rows, each row is list of float values
    """
    headers: list[str] = []
    data_rows: list[list[float]] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip separator lines (all dashes/spaces)
        if all(c in "- " for c in stripped):
            continue
        # Skip Index column headers and extract remaining headers
        if stripped.lower().startswith("index"):
            # Extract headers from this line and next non-separator line
            parts = _SPLIT_RE.split(stripped)
            headers = [p for p in parts if p.lower() != "index"]
            continue

        parts = _SPLIT_RE.split(stripped)
        # If first column is a numeric index, skip it
        first = parts[0] if parts else ""
        if first.isdigit():
            parts = parts[1:]
        values = [_float_or_none(p) for p in parts]
        values = [v for v in values if v is not None]

        if values:
            data_rows.append(values)

    return headers, data_rows


# ---------------------------------------------------------------------------
# .op parser
# ---------------------------------------------------------------------------


def parse_op(raw_output: str) -> dict[str, float]:
    """Parse Xyce .print op output into {probe_name: value}.

    Xyce OP format:
        Index   V(out)
        ------  ------
             0  3.14159

    Returns an empty dict on failure to parse.
    """
    lines = raw_output.splitlines()
    headers, data_rows = _parse_table(lines)

    if not headers or not data_rows:
        return {}

    # Take the last row (steady-state)
    values = data_rows[-1]

    result: dict[str, float] = {}
    for i, header in enumerate(headers):
        if i < len(values):
            result[header] = values[i]

    return result


# ---------------------------------------------------------------------------
# .ac parser
# ---------------------------------------------------------------------------


def parse_ac(raw_output: str) -> dict[str, list[tuple[float, float]]]:
    """Parse Xyce .print ac output into {probe: [(freq_hz, mag_db), ...]}.

    Xyce AC format:
        Index   FREQ            V(out)
        ------  --------        ------
             0  1.000000e-02    9.999987e-01
             1  1.258925e-02    9.999978e-01

    Each probe maps to a list of (frequency_hz, magnitude_db) tuples.
    The first column after FREQ is assumed to be magnitude in dB.
    If a second value column exists, it is assumed to be phase in degrees
    (appended as (freq, phase_deg) to a separate "<probe>_phase" key).

    Returns empty dict on failure.
    """
    lines = raw_output.splitlines()
    headers, data_rows = _parse_table(lines)

    if not headers or not data_rows:
        return {}

    # First header is FREQ, remaining are probe names
    if len(headers) < 2:
        return {}

    freq_idx = 0
    probe_headers = headers[1:]

    result: dict[str, list[tuple[float, float]]] = {}
    for probe in probe_headers:
        result[probe] = []

    for row in data_rows:
        if len(row) < 2:
            continue
        freq = row[freq_idx]
        for i, probe in enumerate(probe_headers):
            val_idx = i + 1
            if val_idx < len(row):
                result[probe].append((freq, row[val_idx]))

    return result


# ---------------------------------------------------------------------------
# .tran parser
# ---------------------------------------------------------------------------


def parse_tran(raw_output: str) -> dict[str, list[tuple[float, float]]]:
    """Parse Xyce .print tran output into {probe: [(time_s, value), ...]}.

    Xyce TRAN format:
        Index   TIME            V(out)          V(in)
        ------  --------        --------        --------
             0  0.000000e+00    0.000000e+00    0.000000e+00
             1  1.666667e-05    8.543210e-02    6.226000e+00

    Each probe maps to a list of (time_s, value) tuples.

    Returns empty dict on failure.
    """
    lines = raw_output.splitlines()
    headers, data_rows = _parse_table(lines)

    if not headers or not data_rows:
        return {}

    if len(headers) < 2:
        return {}

    time_idx = 0
    probe_headers = headers[1:]

    result: dict[str, list[tuple[float, float]]] = {}
    for probe in probe_headers:
        result[probe] = []

    for row in data_rows:
        if len(row) < 2:
            continue
        time_val = row[time_idx]
        for i, probe in enumerate(probe_headers):
            val_idx = i + 1
            if val_idx < len(row):
                result[probe].append((time_val, row[val_idx]))

    return result
