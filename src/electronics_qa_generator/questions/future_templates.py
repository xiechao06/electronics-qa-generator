"""Question templates for additional circuit topologies — humanized phrasing.

All question text is hand-written in natural, exam-style English matching
the tone of MMMU Electronics benchmark questions. The LLM is never used to
create or rephrase questions. Answers are always computed deterministically
from simulation facts via the CLEVR-style program engine.

To activate a topology:
  1. Implement the CircuitTemplate in templates/
  2. Implement the fact extractor in extraction/facts.py
  3. The templates here are already merged into QUESTION_TEMPLATES at import time.
"""

from __future__ import annotations

from . import programs as P

# ---------------------------------------------------------------------------
# RC step response
# Facts expected: tau_s, v_C_initial, v_C_final, v_C_at_1tau
# ---------------------------------------------------------------------------

RC_STEP_RESPONSE: list[dict] = [
    {
        "id": "rc_step_tau",
        "question_type": "direct",
        "question_template": (
            "The circuit above shows an RC network subjected to a step input. "
            "Determine the time constant τ = RC. Express your answer "
            "in milliseconds to three decimal places."
        ),
        "program": [
            P.read_fact("tau_s"),
            P.push_const(1000.0),
            P.mul("$0", "1000"),
            P.format_numeric("$1", unit="ms", precision=3),
        ],
        "answer_keys": ["tau_s"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rc_step_initial_v",
        "question_type": "direct",
        "question_template": (
            "At the instant immediately after the switch closes (t = 0⁺), "
            "what is the voltage across the capacitor, v_C(0⁺)? "
            "State your answer in volts to three decimal places."
        ),
        "program": [
            P.read_fact("v_C_initial"),
            P.format_numeric("$0", unit="V", precision=3),
        ],
        "answer_keys": ["v_C_initial"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rc_step_final_v",
        "question_type": "direct",
        "question_template": (
            "The input steps from 0 to {V_step} V at t = 0. "
            "After the transient has fully decayed (t → ∞), what is the "
            "steady-state capacitor voltage v_C(∞)? "
            "Report your answer in volts to three decimal places."
        ),
        "program": [
            P.read_fact("v_C_final"),
            P.format_numeric("$0", unit="V", precision=3),
        ],
        "answer_keys": ["v_C_final"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rc_step_v_at_1tau",
        "question_type": "direct",
        "question_template": (
            "The input steps from 0 to {V_step} V at t = 0. "
            "One time constant after the step (t = τ), what is the "
            "capacitor voltage v_C(τ)? Express your answer in volts "
            "to three decimal places."
        ),
        "program": [
            P.read_fact("v_C_at_1tau"),
            P.format_numeric("$0", unit="V", precision=3),
        ],
        "answer_keys": ["v_C_at_1tau"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rc_step_tau_compare",
        "question_type": "comparison",
        "question_template": (
            "Is the time constant τ of this RC circuit greater than 1 ms? Answer yes or no."
        ),
        "program": [
            P.read_fact("tau_s"),
            P.push_const(0.001),
            P.compare(">"),
            P.return_bool("$2", true_label="yes", false_label="no"),
        ],
        "answer_keys": ["tau_s"],
        "answer_formatter": "boolean",
    },
]

# ---------------------------------------------------------------------------
# RL step response
# Facts expected: tau_s (=L/R), i_L_initial, i_L_final, i_L_at_1tau, R_load_ohm
# ---------------------------------------------------------------------------

RL_STEP_RESPONSE: list[dict] = [
    {
        "id": "rl_step_tau",
        "question_type": "direct",
        "question_template": (
            "The circuit above shows an RL network responding to a step input. "
            "Determine the time constant τ = L / R. Express your answer "
            "in milliseconds to three decimal places."
        ),
        "program": [
            P.read_fact("tau_s"),
            P.push_const(1000.0),
            P.mul("$0", "1000"),
            P.format_numeric("$1", unit="ms", precision=3),
        ],
        "answer_keys": ["tau_s"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rl_step_final_i",
        "question_type": "direct",
        "question_template": (
            "The input steps from 0 to {V_step} V at t = 0. "
            "After the transient has fully decayed (t → ∞), what is the "
            "steady-state current through the inductor i_L(∞)? "
            "Report your answer in amperes to three decimal places."
        ),
        "program": [
            P.read_fact("i_L_final"),
            P.format_numeric("$0", unit="A", precision=3),
        ],
        "answer_keys": ["i_L_final"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rl_step_initial_i",
        "question_type": "direct",
        "question_template": (
            "At the instant immediately after the switch closes (t = 0⁺), "
            "what is the inductor current i_L(0⁺)? State your answer "
            "in amperes to three decimal places."
        ),
        "program": [
            P.read_fact("i_L_initial"),
            P.format_numeric("$0", unit="A", precision=3),
        ],
        "answer_keys": ["i_L_initial"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rl_step_power_at_t",
        "question_type": "derived",
        "question_template": (
            "The input steps from 0 to {V_step} V at t = 0. "
            "At t = τ (one time constant after the step), compute the "
            "instantaneous power P = i²R absorbed by the resistor. "
            "Express your answer in watts to three decimal places."
        ),
        "program": [
            P.read_fact("i_L_at_1tau"),
            P.read_fact("i_L_at_1tau"),
            P.mul("$0", "$1"),
            P.read_fact("R_load_ohm"),
            P.mul("$2", "$3"),
            P.format_numeric("$4", unit="W", precision=3),
        ],
        "answer_keys": ["i_L_at_1tau", "R_load_ohm"],
        "answer_formatter": "numeric",
    },
]

# ---------------------------------------------------------------------------
# AC phasor — RC circuit
# Facts expected: V_C_mag_V, V_C_phase_deg, V_R_mag_V, Z_mag_ohm, P_avg_mW
# ---------------------------------------------------------------------------

AC_PHASOR_RC: list[dict] = [
    {
        "id": "phasor_vc_amplitude",
        "question_type": "direct",
        "question_template": (
            "The schematic shows an RC circuit driven by an AC source. "
            "Determine the amplitude (magnitude) of the phasor voltage "
            "V_C across the capacitor. Express your answer in volts "
            "to three decimal places."
        ),
        "program": [
            P.read_fact("V_C_mag_V"),
            P.format_numeric("$0", unit="V", precision=3),
        ],
        "answer_keys": ["V_C_mag_V"],
        "answer_formatter": "numeric",
    },
    {
        "id": "phasor_vc_phase",
        "question_type": "direct",
        "question_template": (
            "What is the phase angle of the capacitor voltage V_C "
            "relative to the source? Express your answer in degrees "
            "to one decimal place."
        ),
        "program": [
            P.read_fact("V_C_phase_deg"),
            P.format_numeric("$0", unit="°", precision=1),
        ],
        "answer_keys": ["V_C_phase_deg"],
        "answer_formatter": "numeric",
    },
    {
        "id": "phasor_z_magnitude",
        "question_type": "direct",
        "question_template": (
            "Compute the magnitude of the total impedance Z_ab looking into "
            "this RC circuit. Report your answer in ohms to two decimal places."
        ),
        "program": [
            P.read_fact("Z_mag_ohm"),
            P.format_numeric("$0", unit="Ω", precision=2),
        ],
        "answer_keys": ["Z_mag_ohm"],
        "answer_formatter": "numeric",
    },
    {
        "id": "phasor_power_avg",
        "question_type": "direct",
        "question_template": (
            "What average power is delivered to the resistor in this "
            "AC-driven RC circuit? State your answer in milliwatts "
            "to two decimal places."
        ),
        "program": [
            P.read_fact("P_avg_mW"),
            P.format_numeric("$0", unit="mW", precision=2),
        ],
        "answer_keys": ["P_avg_mW"],
        "answer_formatter": "numeric",
    },
    {
        "id": "phasor_phase_above_zero",
        "question_type": "comparison",
        "question_template": (
            "In this RC circuit, does the capacitor voltage V_C lag "
            "behind the source (i.e., is its phase angle negative)? "
            "Answer 'yes, lagging' or 'no, leading'."
        ),
        "program": [
            P.read_fact("V_C_phase_deg"),
            P.push_const(0.0),
            P.compare("<"),
            P.return_bool("$2", true_label="yes, lagging", false_label="no, leading"),
        ],
        "answer_keys": ["V_C_phase_deg"],
        "answer_formatter": "boolean",
    },
]

# ---------------------------------------------------------------------------
# BJT common-emitter amplifier
# Facts expected: V_CEQ, I_CQ_mA, A_v, operating_region
# ---------------------------------------------------------------------------

BJT_CE_AMPLIFIER: list[dict] = [
    {
        "id": "bjt_ce_vce_q",
        "question_type": "direct",
        "question_template": (
            "Consider the common-emitter amplifier with R1 = {R1_ohm} Ω, "
            "R2 = {R2_ohm} Ω, RC = {RC_ohm} Ω, RE = {RE_ohm} Ω, "
            "VCC = {VCC_dc} V, and β = {beta}. "
            "Determine the quiescent collector-emitter voltage V_CE "
            "at the DC operating point. Report your answer in volts "
            "to two decimal places."
        ),
        "program": [
            P.read_fact("V_CEQ"),
            P.format_numeric("$0", unit="V", precision=2, min_rel_tol=0.07),
        ],
        "answer_keys": ["V_CEQ"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ce_ic_q",
        "question_type": "direct",
        "question_template": (
            "For this BJT common-emitter stage, what is the quiescent "
            "collector current I_C at the DC bias point? "
            "Express your answer in milliamperes to two decimal places."
        ),
        "program": [
            P.read_fact("I_CQ_mA"),
            P.format_numeric("$0", unit="mA", precision=2, min_rel_tol=0.07),
        ],
        "answer_keys": ["I_CQ_mA"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ce_av",
        "question_type": "direct",
        "question_template": (
            "This common-emitter stage is an inverting amplifier. Determine "
            "the magnitude of the small-signal midband voltage gain "
            "|A_v| = |v_out / v_in|. Report the magnitude to two decimal places."
        ),
        "program": [
            P.read_fact("A_v"),
            P.format_numeric("$0", unit=None, precision=2, min_rel_tol=0.15),
        ],
        "answer_keys": ["A_v"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ce_saturation",
        "question_type": "classification",
        "question_template": (
            "Based on the DC operating point, determine the region of "
            "operation for this BJT. Choose one: active, saturation, or cut-off."
        ),
        "program": [
            P.read_fact("operating_region"),
            P.classify("$0", ["active", "saturation", "cut-off"]),
            P.return_label("$1"),
        ],
        "answer_keys": ["operating_region"],
        "answer_formatter": "label",
    },
    {
        "id": "bjt_ce_vce_compare",
        "question_type": "comparison",
        "question_template": (
            "Is V_CE greater than 0.2 V (the typical saturation voltage)? "
            "In other words, is the transistor operating outside "
            "the saturation region? Answer 'yes, active region' or "
            "'no, saturated'."
        ),
        "program": [
            P.read_fact("V_CEQ"),
            P.push_const(0.2),
            P.compare(">"),
            P.return_bool("$2", true_label="yes, active region", false_label="no, saturated"),
        ],
        "answer_keys": ["V_CEQ"],
        "answer_formatter": "boolean",
    },
]

# ---------------------------------------------------------------------------
# BJT emitter follower (common-collector)
# Facts expected: r_out_ohm, A_v, V_CEQ
# ---------------------------------------------------------------------------

BJT_EMITTER_FOLLOWER: list[dict] = [
    {
        "id": "bjt_ef_rout",
        "question_type": "direct",
        "question_template": (
            "For the emitter-follower (common-collector) stage shown (assume "
            "β = {beta}, driven from an ideal source), determine the small-signal "
            "output resistance r_out looking into the emitter terminal. Express "
            "your answer in ohms to one decimal place."
        ),
        "program": [
            P.read_fact("r_out_ohm"),
            P.format_numeric("$0", unit="Ω", precision=1, min_rel_tol=0.15),
        ],
        "answer_keys": ["r_out_ohm"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ef_av",
        "question_type": "direct",
        "question_template": (
            "An ideal emitter follower has a voltage gain close to unity. "
            "For the stage shown (assume β = {beta}), determine the actual "
            "small-signal voltage gain A_v of this emitter follower. Report "
            "your answer to four decimal places."
        ),
        "program": [
            P.read_fact("A_v"),
            P.format_numeric("$0", unit=None, precision=4, min_rel_tol=0.02),
        ],
        "answer_keys": ["A_v"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ef_gain_near_unity",
        "question_type": "comparison",
        "question_template": (
            "Does this emitter follower achieve a voltage gain greater "
            "than 0.9 V/V? Answer yes or no."
        ),
        "program": [
            P.read_fact("A_v"),
            P.push_const(0.9),
            P.compare(">"),
            P.return_bool("$2"),
        ],
        "answer_keys": ["A_v"],
        "answer_formatter": "boolean",
    },
]

# ---------------------------------------------------------------------------
# MOSFET common-source amplifier
# Facts expected: V_DSQ, I_DQ_mA, A_v
# ---------------------------------------------------------------------------

MOSFET_CS_AMPLIFIER: list[dict] = [
    {
        "id": "mosfet_cs_vds_q",
        "question_type": "direct",
        "question_template": (
            "For the NMOS common-source amplifier shown, determine the "
            "quiescent drain-source voltage V_DS at the DC operating point. "
            "The NMOS has threshold voltage V_TO = 2.0 V and conduction "
            "parameter k_n = 12.5 mA/V^2, with I_D = k_n*(V_GS - V_TO)^2 in "
            "saturation. Report your answer in volts to two decimal places."
        ),
        "program": [
            P.read_fact("V_DSQ"),
            P.format_numeric("$0", unit="V", precision=2, min_rel_tol=0.05),
        ],
        "answer_keys": ["V_DSQ"],
        "answer_formatter": "numeric",
    },
    {
        "id": "mosfet_cs_id_q",
        "question_type": "direct",
        "question_template": (
            "What is the drain current I_D at the quiescent operating point "
            "of this MOSFET amplifier? The NMOS has threshold voltage "
            "V_TO = 2.0 V and conduction parameter k_n = 12.5 mA/V^2, with "
            "I_D = k_n*(V_GS - V_TO)^2 in saturation. Express your answer in "
            "milliamperes to two decimal places."
        ),
        "program": [
            P.read_fact("I_DQ_mA"),
            P.format_numeric("$0", unit="mA", precision=2, min_rel_tol=0.05),
        ],
        "answer_keys": ["I_DQ_mA"],
        "answer_formatter": "numeric",
    },
    {
        "id": "mosfet_cs_av",
        "question_type": "direct",
        "question_template": (
            "This common-source stage is an inverting amplifier. Determine the "
            "magnitude of the small-signal voltage gain |A_v| (the source "
            "resistor is unbypassed). The NMOS has threshold voltage "
            "V_TO = 2.0 V and conduction parameter k_n = 12.5 mA/V^2 "
            "(I_D = k_n*(V_GS - V_TO)^2). Report the magnitude to two decimal "
            "places."
        ),
        "program": [
            P.read_fact("A_v"),
            P.format_numeric("$0", unit=None, precision=2, min_rel_tol=0.10),
        ],
        "answer_keys": ["A_v"],
        "answer_formatter": "numeric",
    },
]

# ---------------------------------------------------------------------------
# Resistor network / Thevenin equivalent
# Facts expected: R_eq_ohm, V_th_V, R_th_ohm, P_source_W
# ---------------------------------------------------------------------------

RESISTOR_NETWORK: list[dict] = [
    {
        "id": "rnet_req",
        "question_type": "direct",
        "question_template": (
            "For the resistor network shown, compute the equivalent "
            "resistance seen looking into the output terminals a-b with the "
            "voltage source replaced by a short circuit and the load resistor "
            "Rload still connected. Express your answer in ohms to three "
            "decimal places."
        ),
        "program": [
            P.read_fact("R_eq_ohm"),
            P.format_numeric("$0", unit="Ω", precision=3),
        ],
        "answer_keys": ["R_eq_ohm"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rnet_vth",
        "question_type": "direct",
        "question_template": (
            "Apply Thevenin's theorem to this resistor network. "
            "Determine the open-circuit voltage V_th appearing "
            "at terminals a-b when the load resistor Rload is removed. "
            "Report your answer in volts to three decimal places."
        ),
        "program": [
            P.read_fact("V_th_V"),
            P.format_numeric("$0", unit="V", precision=3),
        ],
        "answer_keys": ["V_th_V"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rnet_rth",
        "question_type": "direct",
        "question_template": (
            "For the same network, compute the Thevenin equivalent "
            "resistance R_th at terminals a-b, with the load resistor Rload "
            "removed and the voltage source replaced by a short circuit. "
            "Express your answer in ohms to three decimal places."
        ),
        "program": [
            P.read_fact("R_th_ohm"),
            P.format_numeric("$0", unit="Ω", precision=3),
        ],
        "answer_keys": ["R_th_ohm"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rnet_power_source",
        "question_type": "direct",
        "question_template": (
            "How much power is delivered by the voltage source in this "
            "resistor network? State your answer in watts "
            "to three decimal places."
        ),
        "program": [
            P.read_fact("P_source_W"),
            P.format_numeric("$0", unit="W", precision=3),
        ],
        "answer_keys": ["P_source_W"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rnet_rth_compare",
        "question_type": "comparison",
        "question_template": (
            "Is the Thevenin resistance R_th of this network greater than 1 kΩ? Answer yes or no."
        ),
        "program": [
            P.read_fact("R_th_ohm"),
            P.push_const(1000.0),
            P.compare(">"),
            P.return_bool("$2"),
        ],
        "answer_keys": ["R_th_ohm"],
        "answer_formatter": "boolean",
    },
]

# ---------------------------------------------------------------------------
# Op-amp inverting amplifier
# Facts expected: A_v, V_out_dc, f_3dB_hz, configuration
# ---------------------------------------------------------------------------

OP_AMP_INVERTING: list[dict] = [
    {
        "id": "opamp_inv_av",
        "question_type": "direct",
        "question_template": (
            "The schematic shows an op-amp in an inverting amplifier "
            "configuration. Determine the closed-loop voltage gain "
            "A_v = −R_f / R_in. Report your answer to two decimal places."
        ),
        "program": [
            P.read_fact("A_v"),
            P.format_numeric("$0", unit=None, precision=2),
        ],
        "answer_keys": ["A_v"],
        "answer_formatter": "numeric",
    },
    {
        "id": "opamp_inv_vout",
        "question_type": "direct",
        "question_template": (
            "For the inverting amplifier circuit shown, determine the "
            "DC voltage at the output terminal. Express your answer "
            "in volts to three decimal places."
        ),
        "program": [
            P.read_fact("V_out_dc"),
            P.format_numeric("$0", unit="V", precision=3),
        ],
        "answer_keys": ["V_out_dc"],
        "answer_formatter": "numeric",
    },
    {
        "id": "opamp_inv_bw",
        "question_type": "direct",
        "question_template": (
            "What is the −3 dB bandwidth of this inverting amplifier? "
            "Express your answer in hertz to three decimal places."
        ),
        "program": [
            P.read_fact("f_3dB_hz"),
            P.format_numeric("$0", unit="Hz", precision=3),
        ],
        "answer_keys": ["f_3dB_hz"],
        "answer_formatter": "numeric",
    },
    {
        "id": "opamp_inv_inverting",
        "question_type": "classification",
        "question_template": (
            "Identify the configuration of this op-amp circuit: "
            "is it inverting, non-inverting, or a voltage buffer?"
        ),
        "program": [
            P.read_fact("configuration"),
            P.classify("$0", ["inverting", "non-inverting", "buffer"]),
            P.return_label("$1"),
        ],
        "answer_keys": ["configuration"],
        "answer_formatter": "label",
    },
]

# ---------------------------------------------------------------------------
# Series RLC resonance
# Facts expected: f_r_hz, Q, bandwidth_hz, Z_at_resonance_ohm, R_ohm
# ---------------------------------------------------------------------------

RLC_SERIES_RESONANCE: list[dict] = [
    {
        "id": "rlc_res_freq",
        "question_type": "direct",
        "question_template": (
            "The circuit shown is a series RLC network. Determine its "
            "resonant frequency f_r. Express your answer in hertz "
            "to three decimal places."
        ),
        "program": [
            P.read_fact("f_r_hz"),
            P.format_numeric("$0", unit="Hz", precision=3),
        ],
        "answer_keys": ["f_r_hz"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rlc_res_q",
        "question_type": "direct",
        "question_template": (
            "Compute the quality factor Q of this series RLC circuit "
            "at resonance. Report Q to three decimal places."
        ),
        "program": [
            P.read_fact("Q"),
            P.format_numeric("$0", unit=None, precision=3),
        ],
        "answer_keys": ["Q"],
        "answer_formatter": "numeric",
    },
    {
        "id": "rlc_res_bw",
        "question_type": "direct",
        "question_template": (
            "What is the −3 dB bandwidth of this series RLC circuit? "
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
        "id": "rlc_res_z_resistive",
        "question_type": "comparison",
        "question_template": (
            "At resonance, a series RLC circuit presents a purely resistive "
            "impedance equal to R. Is the measured impedance at the resonant "
            "frequency within 5% of the nominal resistance R? "
            "Answer yes or no."
        ),
        "program": [
            P.read_fact("Z_at_resonance_ohm"),
            P.read_fact("R_ohm"),
            P.sub("$0", "$1"),
            P.read_fact("R_ohm"),
            P.push_const(0.05),
            P.mul("$3", "0.05"),
            P.compare("<"),
            P.return_bool("$6", true_label="yes", false_label="no"),
        ],
        "answer_keys": ["Z_at_resonance_ohm", "R_ohm"],
        "answer_formatter": "boolean",
    },
]

# ---------------------------------------------------------------------------
# Full registry of future templates
# ---------------------------------------------------------------------------

FUTURE_QUESTION_TEMPLATES: dict[str, list[dict]] = {
    "rc_step_response": RC_STEP_RESPONSE,
    "rl_step_response": RL_STEP_RESPONSE,
    "ac_phasor_rc": AC_PHASOR_RC,
    "bjt_ce_amplifier": BJT_CE_AMPLIFIER,
    "bjt_emitter_follower": BJT_EMITTER_FOLLOWER,
    "mosfet_cs_amplifier": MOSFET_CS_AMPLIFIER,
    "resistor_network": RESISTOR_NETWORK,
    "op_amp_inverting": OP_AMP_INVERTING,
    "rlc_series_resonance": RLC_SERIES_RESONANCE,
}
