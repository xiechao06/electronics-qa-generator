"""Question template registry — humanized question phrasing.

Each topology maps to a list of question template dicts. Template structure:

    {
        "id": str,                  # unique within topology
        "question_type": str,      # direct | derived | classification | comparison
        "question_template": str,   # text — {param} placeholders for circuit values
        "program": list[dict],      # CLEVR-style program (from .programs)
        "answer_keys": list[str],   # which fact/param keys are used
        "answer_formatter": str,    # numeric | label | boolean
    }

All question text is hand-written in natural, exam-style English.
The LLM is never used to create or rephrase questions — answers are always
computed deterministically from simulation facts via the program engine.
"""

from __future__ import annotations

from . import programs as P
from .future_templates import FUTURE_QUESTION_TEMPLATES

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

QUESTION_TEMPLATES: dict[str, list[dict]] = {
    # ── voltage_divider ────────────────────────────────────────────────
    "voltage_divider": [
        {
            "id": "vd_direct_vout",
            "question_type": "direct",
            "question_template": (
                "Consider the voltage divider network shown in the schematic. "
                "Determine the DC voltage measured at the output node V(out). "
                "Express your answer in volts to three decimal places."
            ),
            "program": [
                P.read_fact("Vout_dc"),
                P.format_numeric("$0", unit="V", precision=3),
            ],
            "answer_keys": ["Vout_dc"],
            "answer_formatter": "numeric",
        },
        {
            "id": "vd_find_vout_given",
            "question_type": "direct",
            "question_template": (
                "A voltage divider is constructed with R1 = {R1_ohm} Ω "
                "and R2 = {R2_ohm} Ω, driven by an input of Vin = {Vin_dc} V. "
                "Calculate the resulting output voltage V(out), "
                "rounded to two decimal places."
            ),
            "program": [
                P.read_fact("Vout_dc"),
                P.format_numeric("$0", unit="V", precision=2),
            ],
            "answer_keys": ["Vout_dc"],
            "answer_formatter": "numeric",
        },
        {
            "id": "vd_derived_ratio",
            "question_type": "derived",
            "question_template": (
                "For the voltage divider shown, compute the attenuation ratio "
                "V(out) ÷ V(in) to four decimal places."
            ),
            "program": [
                P.read_fact("Vout_dc"),
                P.read_fact("Vin_dc"),
                P.div("$0", "$1"),
                P.format_numeric("$2", unit=None, precision=4),
            ],
            "answer_keys": ["Vout_dc", "Vin_dc"],
            "answer_formatter": "numeric",
        },
        {
            "id": "vd_percentage",
            "question_type": "derived",
            "question_template": (
                "In this voltage divider, what fraction of the input appears "
                "at V(out)? State your answer as a percentage, "
                "rounded to one decimal place."
            ),
            "program": [
                P.read_fact("Vout_dc"),
                P.read_fact("Vin_dc"),
                P.div("$0", "$1"),
                P.push_const(100.0),
                P.mul("$2", "100"),
                P.format_numeric("$3", unit=None, precision=1),
            ],
            "answer_keys": ["Vout_dc", "Vin_dc"],
            "answer_formatter": "numeric",
        },
        {
            "id": "vd_comparison_half",
            "question_type": "comparison",
            "question_template": (
                "In this voltage divider, does the output voltage V(out) "
                "exceed one half of the input voltage V(in)? Answer yes or no."
            ),
            "program": [
                P.read_fact("Vout_dc"),
                P.read_fact("Vin_dc"),
                P.push_const(0.5),
                P.mul("$1", "0.5"),
                P.compare(">"),
                P.return_bool("$4"),
            ],
            "answer_keys": ["Vout_dc", "Vin_dc"],
            "answer_formatter": "boolean",
        },
    ],

    # ── rc_lowpass ─────────────────────────────────────────────────────
    "rc_lowpass": [
        {
            "id": "lp_direct_cutoff",
            "question_type": "direct",
            "question_template": (
                "The schematic above shows a first-order RC low-pass filter. "
                "Determine its −3 dB cutoff frequency in hertz to three decimal places."
            ),
            "program": [
                P.read_fact("cutoff_hz"),
                P.format_numeric("$0", unit="Hz", precision=3),
            ],
            "answer_keys": ["cutoff_hz"],
            "answer_formatter": "numeric",
        },
        {
            "id": "lp_theoretical_cutoff",
            "question_type": "direct",
            "question_template": (
                "Recall that the cutoff frequency of an RC low-pass filter is "
                "f_c = 1 / (2πRC). For R = {R1_ohm} Ω and C = {C1_f} F, "
                "compute f_c and round your answer to the nearest integer hertz."
            ),
            "program": [
                P.read_fact("cutoff_hz"),
                P.format_numeric("$0", unit="Hz", precision=0),
            ],
            "answer_keys": ["cutoff_hz"],
            "answer_formatter": "numeric",
        },
        {
            "id": "lp_passband_gain",
            "question_type": "direct",
            "question_template": (
                "What is the passband gain of this low-pass filter, "
                "expressed in decibels? Provide your answer to two decimal places."
            ),
            "program": [
                P.read_fact("passband_gain_db"),
                P.format_numeric("$0", unit="dB", precision=2),
            ],
            "answer_keys": ["passband_gain_db"],
            "answer_formatter": "numeric",
        },
        {
            "id": "lp_classification",
            "question_type": "classification",
            "question_template": (
                "Based on its simulated frequency response, classify this "
                "filter as low-pass, high-pass, or band-pass."
            ),
            "program": [
                P.read_fact("behavior"),
                P.classify("$0", ["low-pass", "high-pass", "band-pass"]),
                P.return_label("$1"),
            ],
            "answer_keys": ["behavior"],
            "answer_formatter": "label",
        },
        {
            "id": "lp_comparison_1khz",
            "question_type": "comparison",
            "question_template": (
                "Does the −3 dB cutoff frequency of this filter lie above "
                "1 kHz? Answer 'above' or 'below'."
            ),
            "program": [
                P.read_fact("cutoff_hz"),
                P.push_const(1000.0),
                P.compare(">"),
                P.return_bool("$2", true_label="above", false_label="below"),
            ],
            "answer_keys": ["cutoff_hz"],
            "answer_formatter": "boolean",
        },
    ],

    # ── rc_highpass ────────────────────────────────────────────────────
    "rc_highpass": [
        {
            "id": "hp_direct_cutoff",
            "question_type": "direct",
            "question_template": (
                "The schematic above shows a first-order RC high-pass filter. "
                "Determine its −3 dB cutoff frequency in hertz to three decimal places."
            ),
            "program": [
                P.read_fact("cutoff_hz"),
                P.format_numeric("$0", unit="Hz", precision=3),
            ],
            "answer_keys": ["cutoff_hz"],
            "answer_formatter": "numeric",
        },
        {
            "id": "hp_theoretical_cutoff",
            "question_type": "direct",
            "question_template": (
                "Recall that the cutoff frequency of an RC high-pass filter is "
                "f_c = 1 / (2πRC). For R = {R1_ohm} Ω and C = {C1_f} F, "
                "compute f_c and round your answer to the nearest integer hertz."
            ),
            "program": [
                P.read_fact("cutoff_hz"),
                P.format_numeric("$0", unit="Hz", precision=0),
            ],
            "answer_keys": ["cutoff_hz"],
            "answer_formatter": "numeric",
        },
        {
            "id": "hp_passband_gain",
            "question_type": "direct",
            "question_template": (
                "What is the passband gain of this high-pass filter, "
                "expressed in decibels? Provide your answer to two decimal places."
            ),
            "program": [
                P.read_fact("passband_gain_db"),
                P.format_numeric("$0", unit="dB", precision=2),
            ],
            "answer_keys": ["passband_gain_db"],
            "answer_formatter": "numeric",
        },
        {
            "id": "hp_classification",
            "question_type": "classification",
            "question_template": (
                "Based on its simulated frequency response, classify this "
                "filter as low-pass, high-pass, or band-pass."
            ),
            "program": [
                P.read_fact("behavior"),
                P.classify("$0", ["low-pass", "high-pass", "band-pass"]),
                P.return_label("$1"),
            ],
            "answer_keys": ["behavior"],
            "answer_formatter": "label",
        },
        {
            "id": "hp_comparison_1khz",
            "question_type": "comparison",
            "question_template": (
                "Does the −3 dB cutoff frequency of this filter lie above "
                "1 kHz? Answer 'above' or 'below'."
            ),
            "program": [
                P.read_fact("cutoff_hz"),
                P.push_const(1000.0),
                P.compare(">"),
                P.return_bool("$2", true_label="above", false_label="below"),
            ],
            "answer_keys": ["cutoff_hz"],
            "answer_formatter": "boolean",
        },
    ],

    # ── rlc_bandpass ───────────────────────────────────────────────────
    "rlc_bandpass": [
        {
            "id": "bp_direct_center",
            "question_type": "direct",
            "question_template": (
                "The circuit shown is a parallel RLC band-pass filter. "
                "Determine its center (resonant) frequency f₀ in hertz "
                "to three decimal places."
            ),
            "program": [
                P.read_fact("center_freq_hz"),
                P.format_numeric("$0", unit="Hz", precision=3),
            ],
            "answer_keys": ["center_freq_hz"],
            "answer_formatter": "numeric",
        },
        {
            "id": "bp_direct_bw",
            "question_type": "direct",
            "question_template": (
                "What is the −3 dB bandwidth of this band-pass filter? "
                "Express your answer in hertz to three decimal places."
            ),
            "program": [
                P.read_fact("bandwidth_hz"),
                P.format_numeric("$0", unit="Hz", precision=3),
            ],
            "answer_keys": ["bandwidth_hz"],
            "answer_formatter": "numeric",
        },
        {
            "id": "bp_derived_q",
            "question_type": "derived",
            "question_template": (
                "Using your measured center frequency and bandwidth, compute "
                "the quality factor Q = f₀ / BW for this RLC band-pass filter. "
                "Report Q to three decimal places."
            ),
            "program": [
                P.read_fact("center_freq_hz"),
                P.read_fact("bandwidth_hz"),
                P.div("$0", "$1"),
                P.format_numeric("$2", unit=None, precision=3),
            ],
            "answer_keys": ["center_freq_hz", "bandwidth_hz"],
            "answer_formatter": "numeric",
        },
        {
            "id": "bp_classification",
            "question_type": "classification",
            "question_template": (
                "Based on its simulated frequency response, classify this "
                "filter as low-pass, high-pass, or band-pass."
            ),
            "program": [
                P.read_fact("behavior"),
                P.classify("$0", ["low-pass", "high-pass", "band-pass"]),
                P.return_label("$1"),
            ],
            "answer_keys": ["behavior"],
            "answer_formatter": "label",
        },
        {
            "id": "bp_comparison_bw",
            "question_type": "comparison",
            "question_template": (
                "Is the −3 dB bandwidth of this filter narrower than 10% "
                "of its center frequency? Answer yes or no."
            ),
            "program": [
                P.read_fact("bandwidth_hz"),
                P.read_fact("center_freq_hz"),
                P.push_const(0.10),
                P.mul("$1", "0.10"),
                P.compare("<"),
                P.return_bool("$4", true_label="yes", false_label="no"),
            ],
            "answer_keys": ["bandwidth_hz", "center_freq_hz"],
            "answer_formatter": "boolean",
        },
    ],

    # ── half_wave_rectifier ────────────────────────────────────────────
    "half_wave_rectifier": [
        {
            "id": "hw_direct_vout_dc",
            "question_type": "direct",
            "question_template": (
                "A half-wave rectifier with a filter capacitor is shown. "
                "Calculate the average (DC) voltage at the output. "
                "Express your answer in volts to three decimal places."
            ),
            "program": [
                P.read_fact("Vout_dc"),
                P.format_numeric("$0", unit="V", precision=3),
            ],
            "answer_keys": ["Vout_dc"],
            "answer_formatter": "numeric",
        },
        {
            "id": "hw_direct_vout_peak",
            "question_type": "direct",
            "question_template": (
                "This half-wave rectifier is driven by a sinusoidal input of "
                "{Vin_amplitude} V amplitude at {Vin_frequency_hz} Hz. "
                "What is the peak voltage observed at the output? "
                "Report your answer in volts to three decimal places."
            ),
            "program": [
                P.read_fact("Vout_peak"),
                P.format_numeric("$0", unit="V", precision=3),
            ],
            "answer_keys": ["Vout_peak"],
            "answer_formatter": "numeric",
        },
        {
            "id": "hw_derived_ripple_ratio",
            "question_type": "derived",
            "question_template": (
                "Using your simulation results, compute the ripple ratio "
                "(peak-to-peak ripple voltage divided by DC output voltage) "
                "for this half-wave rectifier. Round to four decimal places."
            ),
            "program": [
                P.read_fact("ripple_vpp"),
                P.read_fact("Vout_dc"),
                P.div("$0", "$1"),
                P.format_numeric("$2", unit=None, precision=4),
            ],
            "answer_keys": ["ripple_vpp", "Vout_dc"],
            "answer_formatter": "numeric",
        },
        {
            "id": "hw_direct_ripple_mv",
            "question_type": "direct",
            "question_template": (
                "What is the peak-to-peak ripple voltage at the output of this "
                "half-wave rectifier? Express your answer in millivolts, "
                "rounded to one decimal place."
            ),
            "program": [
                P.read_fact("ripple_vpp"),
                P.push_const(1000.0),
                P.mul("$0", "1000"),
                P.format_numeric("$1", unit="mV", precision=1),
            ],
            "answer_keys": ["ripple_vpp"],
            "answer_formatter": "numeric",
        },
        {
            "id": "hw_comparison_ripple",
            "question_type": "comparison",
            "question_template": (
                "Does the peak-to-peak ripple voltage of this rectifier "
                "exceed 10% of the DC output level? Answer yes or no."
            ),
            "program": [
                P.read_fact("ripple_vpp"),
                P.read_fact("Vout_dc"),
                P.push_const(0.10),
                P.mul("$1", "0.10"),
                P.compare(">"),
                P.return_bool("$4", true_label="yes", false_label="no"),
            ],
            "answer_keys": ["ripple_vpp", "Vout_dc"],
            "answer_formatter": "boolean",
        },
    ],
}

# Merge future templates into the active registry
QUESTION_TEMPLATES.update(FUTURE_QUESTION_TEMPLATES)
