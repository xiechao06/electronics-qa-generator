"""Fact extractors: compute canonical ground-truth facts from parsed data.

Each template has a dedicated extractor function that accepts parsed simulation
output and component parameters, and returns a dict of measurable facts.

Shared helpers for cutoff frequency detection are provided at module level.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def find_cutoff_frequency(
    freqs: list[float],
    gains_db: list[float],
) -> float:
    """Find the −3 dB cutoff frequency from an AC sweep.

    For a low-pass response, the reference is the gain at the lowest frequency.
    For a high-pass response, the reference is the maximum gain.
    The function detects which case applies and returns the frequency where
    gain has dropped by 3 dB from the reference.

    If no clear −3 dB point is found (e.g., degenerate sweep), returns 0.0.
    """
    if len(freqs) < 2 or len(gains_db) < 2:
        return 0.0

    ref_gain = max(gains_db)
    threshold = ref_gain - 3.0

    # Find the first crossing below threshold
    for i in range(len(gains_db) - 1):
        g1 = gains_db[i]
        g2 = gains_db[i + 1]
        # Check if we cross the −3 dB line
        if (g1 >= threshold >= g2) or (g2 >= threshold >= g1):
            # Linear interpolation between the two points
            if abs(g2 - g1) < 1e-12:
                return (freqs[i] + freqs[i + 1]) / 2.0
            t = (threshold - g1) / (g2 - g1)
            return freqs[i] + t * (freqs[i + 1] - freqs[i])

    return 0.0


def _classify_behavior(
    gains_db: list[float],
    cutoff_hz: float,
) -> str:
    """Classify filter behavior from AC sweep data.

    Uses gain profile shape as a heuristic:
    - low-pass: gain decreases at high frequencies
    - high-pass: gain increases at high frequencies
    - band-pass: gain peaks in the middle
    - none: cannot determine
    """
    if not gains_db or len(gains_db) < 3:
        return "none"

    early = gains_db[0]
    mid = gains_db[len(gains_db) // 2]
    late = gains_db[-1]

    # Band-pass: mid is significantly higher than both ends
    if mid > early + 6 and mid > late + 6:
        return "band-pass"

    # Low-pass: early is high, late is low
    if early > late + 3:
        return "low-pass"

    # High-pass: late is high, early is low
    if late > early + 3:
        return "high-pass"

    if cutoff_hz > 0:
        return "low-pass"  # default for detected cutoff

    return "none"


# ---------------------------------------------------------------------------
# Per-topology extractors
# ---------------------------------------------------------------------------


def _extract_voltage_divider(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract DC output voltage and divider ratio from .op results."""
    vout = parsed.get("V(OUT)", 0.0)
    vin = params.get("Vin_dc", 1.0)
    return {
        "Vout_dc": vout,
        "divider_ratio": vout / vin if vin else 0.0,
        "Vin_dc": vin,
    }


def _extract_rc_lowpass(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract cutoff frequency, passband gain, and behavior from .ac results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    if not data:
        return {
            "cutoff_hz": 0.0,
            "passband_gain_db": 0.0,
            "behavior": "none",
        }

    freqs = [f for f, _ in data]
    gains = [g for _, g in data]
    fc = find_cutoff_frequency(freqs, gains)
    behavior = _classify_behavior(gains, fc)

    passband_gain = gains[0] if gains else 0.0

    return {
        "cutoff_hz": fc,
        "passband_gain_db": passband_gain,
        "behavior": behavior,
    }


def _extract_rc_highpass(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract cutoff frequency, passband gain, and behavior from .ac results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    if not data:
        return {
            "cutoff_hz": 0.0,
            "passband_gain_db": 0.0,
            "behavior": "none",
        }

    freqs = [f for f, _ in data]
    gains = [g for _, g in data]
    fc = find_cutoff_frequency(freqs, gains)
    behavior = _classify_behavior(gains, fc)

    passband_gain = max(gains) if gains else 0.0

    return {
        "cutoff_hz": fc,
        "passband_gain_db": passband_gain,
        "behavior": behavior,
    }


def _extract_rlc_bandpass(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract center frequency, bandwidth, Q, and peak gain from .ac results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    if not data:
        return {
            "center_freq_hz": 0.0,
            "bandwidth_hz": 0.0,
            "Q": 0.0,
            "peak_gain_db": 0.0,
        }

    freqs = [f for f, _ in data]
    gains = [g for _, g in data]

    # Peak
    peak_idx = max(range(len(gains)), key=lambda i: gains[i])
    peak_freq = freqs[peak_idx]
    peak_gain = gains[peak_idx]
    threshold = peak_gain - 3.0

    # Lower −3 dB point
    fc_low = 0.0
    for i in range(peak_idx, 0, -1):
        g_upper = gains[i]
        g_lower = gains[i - 1]
        if (g_upper >= threshold >= g_lower) or (g_lower >= threshold >= g_upper):
            t = (threshold - g_upper) / (g_lower - g_upper) if g_lower != g_upper else 0
            fc_low = freqs[i] + t * (freqs[i - 1] - freqs[i])
            break

    # Upper −3 dB point
    fc_high = 0.0
    for i in range(peak_idx, len(gains) - 1):
        g_left = gains[i]
        g_right = gains[i + 1]
        if (g_left >= threshold >= g_right) or (g_right >= threshold >= g_left):
            t = (threshold - g_left) / (g_right - g_left) if g_right != g_left else 0
            fc_high = freqs[i] + t * (freqs[i + 1] - freqs[i])
            break

    bandwidth = fc_high - fc_low if fc_low > 0 and fc_high > 0 else 0.0
    q_factor = peak_freq / bandwidth if bandwidth > 0 else 0.0

    return {
        "center_freq_hz": peak_freq,
        "bandwidth_hz": bandwidth,
        "Q": q_factor,
        "peak_gain_db": peak_gain,
    }


def _extract_half_wave_rectifier(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract peak output voltage, DC level, and ripple from .tran results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    if not data:
        return {
            "Vout_peak": 0.0,
            "Vout_dc": 0.0,
            "ripple_vpp": 0.0,
        }

    values = [v for _, v in data]

    # Skip the first 20% as startup transient
    n = len(values)
    steady = values[int(n * 0.2) :] if n > 10 else values

    if not steady:
        return {"Vout_peak": 0.0, "Vout_dc": 0.0, "ripple_vpp": 0.0}

    vout_peak = max(steady)
    vout_dc = sum(steady) / len(steady)
    ripple_vpp = max(steady) - min(steady)

    return {
        "Vout_peak": vout_peak,
        "Vout_dc": vout_dc,
        "ripple_vpp": ripple_vpp,
    }


# ---------------------------------------------------------------------------
# Transient extractors
# ---------------------------------------------------------------------------


def _extract_rc_step_response(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract RC step response facts from .tran results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    tau = params.get("tau_s", 0.0)
    v_step = params.get("V_step", 0.0)

    if not data:
        return {
            "tau_s": tau,
            "v_C_initial": 0.0,
            "v_C_final": v_step,
            "v_C_at_1tau": 0.0,
        }

    times = [t for t, _ in data]
    values = [v for _, v in data]

    # Initial: first data point after t=0
    v_initial = values[0] if values else 0.0

    # Final: last data point
    v_final = values[-1] if values else v_step

    # v_C at t = 1τ — find nearest time point
    v_at_1tau = 0.0
    if tau > 0:
        best_idx = min(range(len(times)), key=lambda i: abs(times[i] - tau))
        v_at_1tau = values[best_idx]

    return {
        "tau_s": tau,
        "v_C_initial": v_initial,
        "v_C_final": v_final,
        "v_C_at_1tau": v_at_1tau,
    }


def _extract_rl_step_response(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract RL step response facts from .tran results."""
    probe_key = "I(L1)"
    data = parsed.get(probe_key, [])

    tau = params.get("tau_s", 0.0)
    r_load = params.get("R_ohm", 0.0)
    v_step = params.get("V_step", 0.0)

    if not data:
        i_final = v_step / r_load if r_load > 0 else 0.0
        return {
            "tau_s": tau,
            "i_L_initial": 0.0,
            "i_L_final": i_final,
            "i_L_at_1tau": 0.0,
            "R_load_ohm": r_load,
        }

    times = [t for t, _ in data]
    values = [v for _, v in data]

    i_initial = values[0] if values else 0.0
    i_final = values[-1] if values else (v_step / r_load if r_load > 0 else 0.0)

    i_at_1tau = 0.0
    if tau > 0:
        best_idx = min(range(len(times)), key=lambda i: abs(times[i] - tau))
        i_at_1tau = values[best_idx]

    return {
        "tau_s": tau,
        "i_L_initial": i_initial,
        "i_L_final": i_final,
        "i_L_at_1tau": i_at_1tau,
        "R_load_ohm": r_load,
    }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


FACT_EXTRACTORS: dict[str, Callable] = {
    "voltage_divider": _extract_voltage_divider,
    "rc_lowpass": _extract_rc_lowpass,
    "rc_highpass": _extract_rc_highpass,
    "rlc_bandpass": _extract_rlc_bandpass,
    "half_wave_rectifier": _extract_half_wave_rectifier,
    "rc_step_response": _extract_rc_step_response,
    "rl_step_response": _extract_rl_step_response,
    "ac_phasor_rc": _extract_rc_lowpass,  # same extraction pattern (series RC, V out)
    "bjt_ce_amplifier": _extract_rc_lowpass,  # placeholder — gain from .ac
    "bjt_emitter_follower": _extract_rc_lowpass,  # placeholder
    "mosfet_cs_amplifier": _extract_rc_lowpass,  # placeholder
    "resistor_network": _extract_voltage_divider,  # .op output voltage
    "op_amp_inverting": _extract_rc_lowpass,  # .ac gain
    "rlc_series_resonance": _extract_rlc_bandpass,  # resonance from .ac
}
"""Registry mapping topology name → fact extractor function.

Each extractor accepts (parsed_output: dict, params: dict) and returns a
dict of canonical facts.
"""
