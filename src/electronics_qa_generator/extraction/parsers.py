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

    # Find the table header line
    header_line_idx: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "Index" in stripped:
            header_line_idx = i
            break

    if header_line_idx is None:
        return {}

    headers, data_rows = _parse_table(lines[header_line_idx:])

    if not headers or not data_rows:
        return {}

    # Take the last row (steady-state)
    values = data_rows[-1]

    result: dict[str, float] = {}
    for i, header in enumerate(headers):
        if i < len(values):
            # Normalize probe names to uppercase for consistency with .ac parser
            result[header.upper()] = values[i]

    return result


# ---------------------------------------------------------------------------
# .ac parser
# ---------------------------------------------------------------------------


def parse_ac(raw_output: str) -> dict[str, list[tuple[float, float]]]:
    """Parse Xyce .print ac output into {probe: [(freq_hz, mag_db), ...]}.

    Xyce AC format (complex columns):
        Index   FREQ            Re(V(out))      Im(V(out))
        ------  --------        ----------      ----------
             0  1.000000e-02    9.999987e-01    -4.27e-05

    Each probe maps to a list of (frequency_hz, magnitude_db) tuples.
    Complex voltage (Re, Im) is combined into a single magnitude in dB.
    """
    import math

    lines = raw_output.splitlines()

    # Find the table start: the line containing "Index" and "FREQ"
    header_line_idx: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "Index" in stripped and ("FREQ" in stripped or "Freq" in stripped):
            header_line_idx = i
            break

    if header_line_idx is None:
        return {}

    # Only parse from the header onward
    headers, data_rows = _parse_table(lines[header_line_idx:])
    if not headers or not data_rows:
        return {}

    # headers: e.g. ["FREQ", "Re(V(OUT))", "Im(V(OUT))"]
    freq_idx = 0

    result: dict[str, list[tuple[float, float]]] = {}

    # Map probe names: strip "Re(" and "Im(" prefixes to group under canonical name
    # e.g., "Re(V(OUT))" and "Im(V(OUT))" → "V(OUT)"
    # Also handle simple magnitude-only headers like "V(out)" or "V(OUT)"
    _header_map: dict[int, str] = {}  # col_idx → canonical probe name
    _re_im_pairs: dict[str, tuple[int, int]] = {}  # canonical_name → (re_col, im_col)

    import re as _re

    for i, h in enumerate(headers):
        if h.upper() == "FREQ":
            continue  # frequency column, not a probe
        m_re = _re.match(r"^\s*Re\(\s*(.+)\s*\)\s*$", h, _re.IGNORECASE)
        m_im = _re.match(r"^\s*Im\(\s*(.+)\s*\)\s*$", h, _re.IGNORECASE)
        if m_re:
            inner = m_re.group(1).strip()
            canonical = inner  # e.g. "V(OUT)"
            pair = _re_im_pairs.setdefault(canonical.upper(), [-1, -1])
            pair[0] = i
        elif m_im:
            inner = m_im.group(1).strip()
            canonical = inner
            pair = _re_im_pairs.setdefault(canonical.upper(), [-1, -1])
            pair[1] = i
        else:
            _header_map[i] = h.upper()

    # Initialize result dict
    for canonical in set(_header_map.values()) | set(_re_im_pairs.keys()):
        result[canonical.upper()] = []

    for row in data_rows:
        if len(row) < 2:
            continue
        freq = row[freq_idx]

        # Fill scalar probes
        for col_idx, canonical in _header_map.items():
            if col_idx < len(row):
                # Treat scalar as dB directly (for simple formats)
                result[canonical.upper()].append((freq, row[col_idx]))

        # Fill complex probe pairs
        for canonical, (re_col, im_col) in _re_im_pairs.items():
            if re_col < len(row) and im_col < len(row):
                re_v = row[re_col]
                im_v = row[im_col]
                mag = math.sqrt(re_v**2 + im_v**2)
                mag_db = 20 * math.log10(mag) if mag > 0 else -200.0
                result[canonical.upper()].append((freq, mag_db))

    return result


def parse_ac_complex(raw_output: str) -> dict[str, list[tuple[float, complex]]]:
    """Parse Xyce .print ac output preserving complex phasors.

    Like :func:`parse_ac`, but instead of collapsing Re/Im into a single
    magnitude (dB), it keeps the full complex value so downstream code can
    derive both magnitude *and* phase. Used for single-frequency phasor
    questions where the phase angle is part of the ground truth.

    Returns ``{probe: [(freq_hz, complex(re, im)), ...]}``.
    """
    lines = raw_output.splitlines()

    header_line_idx: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "Index" in stripped and ("FREQ" in stripped or "Freq" in stripped):
            header_line_idx = i
            break

    if header_line_idx is None:
        return {}

    headers, data_rows = _parse_table(lines[header_line_idx:])
    if not headers or not data_rows:
        return {}

    import re as _re

    freq_idx = 0
    re_im_pairs: dict[str, list[int]] = {}  # canonical → [re_col, im_col]

    for i, h in enumerate(headers):
        if h.upper() == "FREQ":
            continue
        m_re = _re.match(r"^\s*Re\(\s*(.+)\s*\)\s*$", h, _re.IGNORECASE)
        m_im = _re.match(r"^\s*Im\(\s*(.+)\s*\)\s*$", h, _re.IGNORECASE)
        if m_re:
            pair = re_im_pairs.setdefault(m_re.group(1).strip().upper(), [-1, -1])
            pair[0] = i
        elif m_im:
            pair = re_im_pairs.setdefault(m_im.group(1).strip().upper(), [-1, -1])
            pair[1] = i

    result: dict[str, list[tuple[float, complex]]] = {canonical: [] for canonical in re_im_pairs}

    for row in data_rows:
        if len(row) < 2:
            continue
        freq = row[freq_idx]
        for canonical, (re_col, im_col) in re_im_pairs.items():
            if re_col < len(row) and im_col < len(row):
                result[canonical].append((freq, complex(row[re_col], row[im_col])))

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

    # Find the table header line
    header_line_idx: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "Index" in stripped and ("TIME" in stripped or "Time" in stripped):
            header_line_idx = i
            break

    if header_line_idx is None:
        return {}

    headers, data_rows = _parse_table(lines[header_line_idx:])

    if not headers or not data_rows:
        return {}

    if len(headers) < 2:
        return {}

    time_idx = 0
    probe_headers = headers[1:]

    result: dict[str, list[tuple[float, float]]] = {}
    for probe in probe_headers:
        result[probe.upper()] = []

    for row in data_rows:
        if len(row) < 2:
            continue
        time_val = row[time_idx]
        for i, probe in enumerate(probe_headers):
            val_idx = i + 1
            if val_idx < len(row):
                result[probe.upper()].append((time_val, row[val_idx]))

    return result


# ---------------------------------------------------------------------------
# Parser selection
# ---------------------------------------------------------------------------

# Topologies whose facts require the full complex phasor (magnitude + phase)
# rather than magnitude-only AC data.
_COMPLEX_AC_TOPOLOGIES = frozenset({"ac_phasor_rc"})


def get_parser(sim_type: str, topology: str | None = None):
    """Return the appropriate parser for a (sim_type, topology) pair.

    Most AC topologies use :func:`parse_ac` (magnitude in dB). Phasor
    topologies that need the phase angle use :func:`parse_ac_complex`.
    """
    if sim_type == "ac" and topology in _COMPLEX_AC_TOPOLOGIES:
        return parse_ac_complex
    return {"op": parse_op, "ac": parse_ac, "tran": parse_tran}.get(sim_type, parse_op)
