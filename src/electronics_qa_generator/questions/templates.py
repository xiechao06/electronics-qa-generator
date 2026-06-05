"""Question template registry.

Each topology maps to a list of question template dicts. Template structure:

    {
        "id": str,                  # unique within topology
        "question_type": str,      # direct | derived | classification | comparison
        "question_template": str,   # text — {fact} or {param} placeholders
        "program": list[dict],      # CLEVR-style program (from .programs)
        "answer_keys": list[str],   # which fact/param keys are used
        "answer_formatter": str,    # numeric | label | boolean
    }

Question templates are inspired by real MMMU Electronics benchmark phrasing
patterns (77 "find/calculate X" questions, unit specifications, precision
constraints, and comparison prompts).

16 templates inherited from the initial design + 9 new MMMU-inspired templates
for a total of 25 across 5 topologies.
"""

from __future__ import annotations

from . import programs as P
from .future_templates import FUTURE_QUESTION_TEMPLATES

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

QUESTION_TEMPLATES: dict[str, list[dict]] = {
    # ── voltage_divider (5 templates) ──────────────────────────────────
    "voltage_divider": [
        # --- Direct: Vout_dc ---
        {
            "id": "vd_direct_vout",
            "question_type": "direct",
            "question_template": (
                "What is the DC voltage at the output node V(out) of this voltage divider?"
            ),
            "program": [
                P.read_fact("Vout_dc"),
                P.format_numeric("$0", unit="V", precision=3),
            ],
            "answer_keys": ["Vout_dc"],
            "answer_formatter": "numeric",
        },
        # --- Direct with parameter context (MMMU: "given the circuit values, find X") ---
        {
            "id": "vd_find_vout_given",
            "question_type": "direct",
            "question_template": (
                "Given R1 = {R1_ohm} Ω and R2 = {R2_ohm} Ω "
                "with Vin = {Vin_dc} V, find the output voltage V(out). "
                "Provide your answer in volts, rounded to 2 decimal places."
            ),
            "program": [
                P.read_fact("Vout_dc"),
                P.format_numeric("$0", unit="V", precision=2),
            ],
            "answer_keys": ["Vout_dc"],
            "answer_formatter": "numeric",
        },
        # --- Derived: divider ratio ---
        {
            "id": "vd_derived_ratio",
            "question_type": "derived",
            "question_template": (
                "Calculate the voltage divider ratio V(out) / V(in) for this circuit."
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
        # --- Derived: Vout as percentage (MMMU: "in terms of X") ---
        {
            "id": "vd_percentage",
            "question_type": "derived",
            "question_template": (
                "What percentage of the input voltage appears at V(out)? Round to 1 decimal place."
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
        # --- Comparison ---
        {
            "id": "vd_comparison_half",
            "question_type": "comparison",
            "question_template": ("Is V(out) greater than half of V(in)?"),
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
    # ── rc_lowpass (5 templates) ───────────────────────────────────────
    "rc_lowpass": [
        # --- Direct cutoff ---
        {
            "id": "lp_direct_cutoff",
            "question_type": "direct",
            "question_template": ("Find the −3 dB cutoff frequency of this RC low-pass filter."),
            "program": [
                P.read_fact("cutoff_hz"),
                P.format_numeric("$0", unit="Hz", precision=3),
            ],
            "answer_keys": ["cutoff_hz"],
            "answer_formatter": "numeric",
        },
        # --- Direct with theoretical comparison (MMMU: "compare to formula") ---
        {
            "id": "lp_theoretical_cutoff",
            "question_type": "direct",
            "question_template": (
                "The theoretical cutoff is fc = 1/(2πRC). "
                "With R = {R1_ohm} Ω and C = {C1_f} F, calculate fc. "
                "Provide your answer in hertz, rounded to the nearest integer."
            ),
            "program": [
                P.read_fact("cutoff_hz"),
                P.format_numeric("$0", unit="Hz", precision=0),
            ],
            "answer_keys": ["cutoff_hz"],
            "answer_formatter": "numeric",
        },
        # --- Derived: passband gain correctness check ---
        {
            "id": "lp_passband_gain",
            "question_type": "direct",
            "question_template": ("What is the passband gain of this filter in dB?"),
            "program": [
                P.read_fact("passband_gain_db"),
                P.format_numeric("$0", unit="dB", precision=2),
            ],
            "answer_keys": ["passband_gain_db"],
            "answer_formatter": "numeric",
        },
        # --- Classification ---
        {
            "id": "lp_classification",
            "question_type": "classification",
            "question_template": ("Classify the frequency response behavior of this filter."),
            "program": [
                P.read_fact("behavior"),
                P.classify("$0", ["low-pass", "high-pass", "band-pass"]),
                P.return_label("$1"),
            ],
            "answer_keys": ["behavior"],
            "answer_formatter": "label",
        },
        # --- Comparison ---
        {
            "id": "lp_comparison_1khz",
            "question_type": "comparison",
            "question_template": ("Is the cutoff frequency of this filter above 1 kHz?"),
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
    # ── rc_highpass (5 templates) ──────────────────────────────────────
    "rc_highpass": [
        {
            "id": "hp_direct_cutoff",
            "question_type": "direct",
            "question_template": ("Find the −3 dB cutoff frequency of this RC high-pass filter."),
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
                "The theoretical cutoff is fc = 1/(2πRC). "
                "With R = {R1_ohm} Ω and C = {C1_f} F, calculate fc. "
                "Provide your answer in hertz, rounded to the nearest integer."
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
            "question_template": ("What is the passband gain of this filter in dB?"),
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
            "question_template": ("Classify the frequency response behavior of this filter."),
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
            "question_template": ("Is the cutoff frequency of this filter above 1 kHz?"),
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
    # ── rlc_bandpass (5 templates) ─────────────────────────────────────
    "rlc_bandpass": [
        {
            "id": "bp_direct_center",
            "question_type": "direct",
            "question_template": (
                "Find the center (resonant) frequency "
                "of this RLC band-pass filter. Provide your answer in Hz."
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
            "question_template": ("What is the −3 dB bandwidth of this band-pass filter?"),
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
                "Calculate the quality factor Q = fc / BW of this RLC band-pass filter."
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
            "question_template": ("Classify the frequency response behavior of this filter."),
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
            "question_template": ("Is the bandwidth less than 10% of the center frequency?"),
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
    # ── half_wave_rectifier (5 templates) ──────────────────────────────
    "half_wave_rectifier": [
        {
            "id": "hw_direct_vout_dc",
            "question_type": "direct",
            "question_template": (
                "Calculate the average (DC) output voltage "
                "of this half-wave rectifier. Provide your answer in volts."
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
                "What is the peak output voltage of this half-wave rectifier, "
                "given an input of {Vin_amplitude} V amplitude at {Vin_frequency_hz} Hz?"
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
                "Calculate the ripple ratio (peak-to-peak ripple / DC output) "
                "of this half-wave rectifier. Round to 4 decimal places."
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
                "What is the peak-to-peak ripple voltage? "
                "Provide your answer in millivolts, rounded to 1 decimal place."
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
                "Does the peak-to-peak ripple exceed 10% of the DC output voltage?"
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
