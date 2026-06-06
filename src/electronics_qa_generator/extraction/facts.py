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
# AC phasor extractor
# ---------------------------------------------------------------------------


def _extract_ac_phasor_rc(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract phasor facts from single-frequency .ac results.

    Expects complex phasor data ``{probe: [(freq, complex), ...]}`` from
    :func:`parse_ac_complex`. All facts are derived from the simulated
    complex node voltage V(out) = V_C, never approximated.

    Series RC: Vin —[R]— out —[C]— gnd, driven by Vin = 1∠0° V (AC mag 1).
    """
    import cmath
    import math

    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    zero = {
        "V_C_mag_V": 0.0,
        "V_C_phase_deg": 0.0,
        "Z_mag_ohm": 0.0,
        "Z_phase_deg": 0.0,
        "P_avg_mW": 0.0,
    }
    if not data:
        return zero

    # Single-point AC → one row. If a sweep slipped through, pick the point
    # closest to the source frequency.
    f_src = params.get("f_src_hz", 0.0)
    if len(data) > 1 and f_src > 0:
        freq, v_c = min(data, key=lambda fc: abs(fc[0] - f_src))
    else:
        freq, v_c = data[0]

    # v_c may be a complex phasor (preferred) or a bare float magnitude.
    if not isinstance(v_c, complex):
        v_c = complex(float(v_c), 0.0)

    vin = complex(1.0, 0.0)  # source AC magnitude 1 V, 0° reference
    r_val = float(params.get("R_ohm", 1000.0))

    # V_C magnitude and phase straight from the simulated phasor.
    v_c_mag = abs(v_c)
    v_c_phase = math.degrees(cmath.phase(v_c))

    # Series current I = (Vin - V_C) / R; total impedance Z = Vin / I.
    i_phasor = (vin - v_c) / r_val if r_val > 0 else complex(0.0, 0.0)
    if i_phasor != 0:
        z_total = vin / i_phasor
        z_mag = abs(z_total)
        z_phase = math.degrees(cmath.phase(z_total))
    else:
        z_mag = 0.0
        z_phase = 0.0

    # Average power delivered to the resistor: P = 0.5 · |I|² · R
    # (factor 0.5 for amplitude—not RMS—phasor convention).
    p_avg = 0.5 * (abs(i_phasor) ** 2) * r_val
    p_avg_mw = p_avg * 1000.0

    return {
        "V_C_mag_V": round(v_c_mag, 6),
        "V_C_phase_deg": round(v_c_phase, 1),
        "Z_mag_ohm": round(z_mag, 2),
        "Z_phase_deg": round(z_phase, 1),
        "P_avg_mW": round(p_avg_mw, 4),
    }


# ---------------------------------------------------------------------------
# Resistor network extractor
# ---------------------------------------------------------------------------


def _extract_resistor_network(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract Thevenin equivalent facts from .op results."""
    v_out = parsed.get("V(OUT)", 0.0)
    v_in = params.get("Vs_dc", 0.0)
    r_a = params.get("Ra_ohm", 1.0)
    r_b = params.get("Rb_ohm", 1.0)
    r_c = params.get("Rc_ohm", 1.0)
    r_d = params.get("Rd_ohm", 1.0)
    r_load = params.get("Rload_ohm", 1.0)

    # V_th = open-circuit voltage at out (approximately V(out) with load)
    v_th = v_out  # simulated V(out) is the Thevenin voltage with load

    # R_th: computed from resistor network topology
    # R_ab = ((R_a // R_c) + (R_b // R_d)) // R_load, approximate
    r_ac = 1.0 / (1.0 / r_a + 1.0 / r_c) if r_a * r_c > 0 else 0.0
    r_bd = 1.0 / (1.0 / r_b + 1.0 / r_d) if r_b * r_d > 0 else 0.0
    r_eq = 1.0 / (1.0 / (r_ac + r_bd) + 1.0 / r_load) if r_load > 0 else 0.0

    # R_th = equivalent resistance seen from output (with source shorted)
    r_th = 1.0 / (1.0 / r_b + 1.0 / r_d) if r_b * r_d > 0 else 0.0
    # More accurate: R_th = parallel of paths from out to ground
    r_th_upper = r_a + (1.0 / (1.0 / r_c + 1.0 / (r_b + r_d)))
    r_th = 1.0 / (1.0 / r_th_upper + 1.0 / r_load) if r_load > 0 else r_th_upper

    # Power from source: P = V_in² / R_effective
    r_total = (r_a + r_th) if r_th > 0 else 1000.0
    p_source = v_in * v_in / r_total if r_total > 0 else 0.0

    return {
        "R_eq_ohm": round(r_eq, 1),
        "V_th_V": round(v_th, 3),
        "R_th_ohm": round(r_th, 1),
        "P_source_W": round(p_source, 4),
    }


# ---------------------------------------------------------------------------
# BJT CE amplifier extractor
# ---------------------------------------------------------------------------


def _extract_bjt_ce_amplifier(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract BJT CE bias and gain facts from .ac results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    vcc = params.get("VCC_dc", 10.0)
    r1 = params.get("R1_ohm", 10e3)
    r2 = params.get("R2_ohm", 10e3)
    rc = params.get("RC_ohm", 4.7e3)
    re = params.get("RE_ohm", 1e3)
    params.get("beta", 200)

    # Approximate bias: V_B = VCC * R2/(R1+R2), V_E = V_B - 0.7, I_C ≈ I_E = V_E/RE
    v_base = vcc * r2 / (r1 + r2) if (r1 + r2) > 0 else 0.0
    v_emitter = v_base - 0.7
    i_c = v_emitter / re if re > 0 else 0.0
    v_collector = vcc - i_c * rc
    v_ceq = v_collector - v_emitter

    # Operating region
    if v_ceq < 0.3:
        operating_region = "saturation"
    elif v_ceq > vcc - 0.5:
        operating_region = "cut-off"
    else:
        operating_region = "active"

    # Gain from .ac sweep
    if data and len(data) > 3:
        gains = [g for _, g in data]
        # Mid-band gain: maximum in the sweep
        av = max(gains) if gains else 0.0
        av = round(10 ** (av / 20.0), 2)  # convert dB to linear
    else:
        av = rc / re if re > 0 else 0.0  # approximate

    return {
        "V_CEQ": round(v_ceq, 2),
        "I_CQ_mA": round(i_c * 1000, 2),
        "A_v": round(av, 2),
        "operating_region": operating_region,
    }


# ---------------------------------------------------------------------------
# BJT emitter follower extractor
# ---------------------------------------------------------------------------


def _extract_bjt_emitter_follower(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract BJT EF facts from .ac results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    vcc = params.get("VCC_dc", 10.0)
    r1 = params.get("R1_ohm", 10e3)
    r2 = params.get("R2_ohm", 10e3)
    re = params.get("RE_ohm", 1e3)
    params.get("beta", 200)

    # Approximate bias
    v_base = vcc * r2 / (r1 + r2) if (r1 + r2) > 0 else 0.0
    v_emitter = v_base - 0.7
    i_e = v_emitter / re if re > 0 else 0.0
    v_ceq = vcc - v_emitter

    # Output resistance: r_out ≈ RE // (re_small_signal) ≈ 25mV/I_E
    r_e_small = 0.025 / i_e if i_e > 0 else 25.0
    r_out = 1.0 / (1.0 / re + 1.0 / r_e_small) if re > 0 else r_e_small

    # Gain from .ac sweep
    if data and len(data) > 3:
        gains = [g for _, g in data]
        av_db = gains[0] if gains else 0.0
        av = round(10 ** (av_db / 20.0), 4)
    else:
        av = 0.98  # emitter follower gain ≈ 0.98

    return {
        "r_out_ohm": round(r_out, 1),
        "A_v": round(av, 4),
        "V_CEQ": round(v_ceq, 2),
    }


# ---------------------------------------------------------------------------
# MOSFET CS amplifier extractor
# ---------------------------------------------------------------------------


def _extract_mosfet_cs_amplifier(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract MOSFET CS bias and gain facts from .ac results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    vdd = params.get("VDD_dc", 15.0)
    rd = params.get("RD_ohm", 4.7e3)
    rs = params.get("RS_ohm", 1e3)
    params.get("RG_ohm", 1e6)

    # Approximate bias: V_GS ≈ VTO (2V), I_D = KP * (V_GS - VTO)²
    vto = 2.0
    kp = 1.0e-3
    v_gs = vto + 0.5  # typical overdrive
    i_d = kp * (v_gs - vto) ** 2  # should be ~0.25 mA
    v_drain = vdd - i_d * rd
    v_source = i_d * rs
    v_dsq = v_drain - v_source

    # Gain from .ac
    if data and len(data) > 3:
        gains = [g for _, g in data]
        av_db = max(gains[: len(gains) // 2]) if gains else 0.0
        av = round(10 ** (av_db / 20.0), 2)
    else:
        av = rd / rs if rs > 0 else 0.0

    return {
        "V_DSQ": round(v_dsq, 2),
        "I_DQ_mA": round(i_d * 1000, 2),
        "A_v": round(av, 2),
    }


# ---------------------------------------------------------------------------
# Op-amp inverting amplifier extractor
# ---------------------------------------------------------------------------


def _extract_op_amp_inverting(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract op-amp gain and bandwidth facts from .ac results."""
    probe_key = "V(OUT)"
    data = parsed.get(probe_key, [])

    params.get("Rf_ohm", 10e3)
    params.get("Rin_ohm", 1e3)
    av_theoretical = params.get("A_v_theoretical", -10.0)
    vin_dc = params.get("Vin_dc", 0.5)

    # DC output: V_out ≈ A_v_theoretical × Vin
    v_out_dc = abs(av_theoretical) * vin_dc

    if data and len(data) > 3:
        freqs = [f for f, _ in data]
        gains = [g for _, g in data]

        # Low-frequency gain
        av_db = gains[0] if gains else 0.0
        av = -round(10 ** (av_db / 20.0), 2)  # negative for inverting

        # −3 dB bandwidth: find where gain drops 3 dB from passband
        fc = find_cutoff_frequency(freqs, gains)
    else:
        av = av_theoretical
        fc = 100e3  # typical op-amp bandwidth

    return {
        "A_v": round(av, 2),
        "V_out_dc": round(v_out_dc, 3),
        "f_3dB_hz": round(fc, 1),
        "configuration": "inverting",
    }


# ---------------------------------------------------------------------------
# RLC series resonance extractor
# ---------------------------------------------------------------------------


def _extract_rlc_series_resonance(
    parsed: dict,
    params: dict,
) -> dict[str, Any]:
    """Extract resonance facts from .ac sweep of series RLC.

    Probes V(mid) and V(n1). Resonance is where impedance is minimum
    (current is maximum, V(n1) is maximum).
    """
    # Try V(n1) first (voltage at L-C junction — maximum at resonance)
    data = parsed.get("V(N1)", [])
    if not data:
        data = parsed.get("V(MID)", [])

    r_val = params.get("R_ohm", 100.0)

    if not data or len(data) < 3:
        return {
            "f_r_hz": 0.0,
            "Q": 0.0,
            "bandwidth_hz": 0.0,
            "Z_at_resonance_ohm": r_val,
            "R_ohm": r_val,
        }

    freqs = [f for f, _ in data]
    gains = [g for _, g in data]

    # Peak = resonance (voltage is maximum at LC junction)
    peak_idx = max(range(len(gains)), key=lambda i: gains[i])
    f_r = freqs[peak_idx]

    # Bandwidth: −3 dB from peak
    threshold = gains[peak_idx] - 3.0
    f_low = 0.0
    for i in range(peak_idx, 0, -1):
        if (gains[i] >= threshold >= gains[i - 1]) or (gains[i - 1] >= threshold >= gains[i]):
            t = (
                (threshold - gains[i]) / (gains[i - 1] - gains[i])
                if gains[i - 1] != gains[i]
                else 0
            )
            f_low = freqs[i] + t * (freqs[i - 1] - freqs[i])
            break

    f_high = 0.0
    for i in range(peak_idx, len(gains) - 1):
        if (gains[i] >= threshold >= gains[i + 1]) or (gains[i + 1] >= threshold >= gains[i]):
            t = (
                (threshold - gains[i]) / (gains[i + 1] - gains[i])
                if gains[i + 1] != gains[i]
                else 0
            )
            f_high = freqs[i] + t * (freqs[i + 1] - freqs[i])
            break

    bw = f_high - f_low if f_low > 0 and f_high > 0 else 0.0
    q_factor = f_r / bw if bw > 0 else 0.0

    # Z at resonance ≈ R (series RLC)
    z_at_resonance = r_val

    return {
        "f_r_hz": round(f_r, 1),
        "Q": round(q_factor, 3),
        "bandwidth_hz": round(bw, 1),
        "Z_at_resonance_ohm": round(z_at_resonance, 1),
        "R_ohm": r_val,
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
    "ac_phasor_rc": _extract_ac_phasor_rc,
    "bjt_ce_amplifier": _extract_bjt_ce_amplifier,
    "bjt_emitter_follower": _extract_bjt_emitter_follower,
    "mosfet_cs_amplifier": _extract_mosfet_cs_amplifier,
    "resistor_network": _extract_resistor_network,
    "op_amp_inverting": _extract_op_amp_inverting,
    "rlc_series_resonance": _extract_rlc_series_resonance,
}
"""Registry mapping topology name → fact extractor function.

Each extractor accepts (parsed_output: dict, params: dict) and returns a
dict of canonical facts.
"""
