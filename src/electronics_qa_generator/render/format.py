"""Human-readable component label formatting for schematic rendering.

Reuses engineering-unit logic from ``graph/spice_emitter.py`` but appends
unit suffixes for display on schematic images (e.g. "4.7k Ω", "100n F").
"""

from __future__ import annotations

from ..graph.spice_emitter import (
    _fmt_capacitance,
    _fmt_frequency,
    _fmt_inductance,
    _fmt_resistance,
    _fmt_voltage,
)

__all__ = [
    "format_component_label",
    "_fmt_resistance",
    "_fmt_capacitance",
    "_fmt_inductance",
    "_fmt_voltage",
    "_fmt_frequency",
]

# .4g can produce trailing zeros like "10.00k" for integer values.
# Strip them for cleaner labels.
import re as _re


def _clean_g(value: str) -> str:
    """Strip insignificant trailing zeros from a .4g-formatted string."""
    return _re.sub(r"\.0+(?=\D|$)", "", value)


def format_component_label(ref: str, kind: str, params: dict) -> str:
    """Return a human-readable label like "R1 4.7k Ω" or "C1 100n F".

    Parameters
    ----------
    ref : str
        Reference designator (e.g. ``"R1"``).
    kind : str
        Component kind: ``"resistor"``, ``"capacitor"``, ``"inductor"``,
        ``"vsource"``, ``"diode"``.
    params : dict
        Component parameters dict (from ``Component.params``).
    """
    if kind == "resistor":
        val = _clean_g(_fmt_resistance(params["value"]))
        return f"{ref} {val} \u03a9"
    if kind == "capacitor":
        val = _clean_g(_fmt_capacitance(params["value"]))
        return f"{ref} {val} F"
    if kind == "inductor":
        val = _clean_g(_fmt_inductance(params["value"]))
        return f"{ref} {val} H"
    if kind == "vsource":
        parts = []
        if "dc" in params:
            parts.append(f"{_clean_g(_fmt_voltage(params['dc']))}V DC")
        if "ac" in params:
            parts.append(f"{_clean_g(_fmt_voltage(params['ac']))}V AC")
        if "sin" in params:
            s = params["sin"]
            amp = _clean_g(_fmt_voltage(s["amplitude"]))
            freq = _clean_g(_fmt_frequency(s["freq"]))
            parts.append(f"{amp}V {freq}Hz")
        suffix = " " + " ".join(parts) if parts else ""
        return f"{ref}{suffix}"
    if kind == "diode":
        model = params.get("model", "")
        if model:
            return f"{ref} {model}"
        return ref
    if kind == "isource":
        parts = []
        if "dc" in params:
            dc_val = params["dc"]
            parts.append(f"{_clean_g(f'{dc_val:.4g}')}A DC")
        if "ac" in params:
            ac_val = params["ac"]
            parts.append(f"{_clean_g(f'{ac_val:.4g}')}A AC")
        suffix = " " + " ".join(parts) if parts else ""
        return f"{ref}{suffix}"
    return ref
    return ref
