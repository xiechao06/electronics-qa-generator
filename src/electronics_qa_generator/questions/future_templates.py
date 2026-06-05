"""Question templates for future circuit topologies.

These templates are grounded in MMMU Electronics benchmark question patterns
(mined from assets/mmmu_electronics_unpacked/, 194 circuit questions).

Each topology listed here does NOT yet have a corresponding CircuitTemplate
or FACT_EXTRACTOR. The templates are defined now so question structure is
agreed before implementation. To activate a topology:
  1. Implement the CircuitTemplate in templates/
  2. Implement the fact extractor in extraction/facts.py
  3. Move the topology entry into QUESTION_TEMPLATES in templates.py

Fact keys expected per topology are documented in comments.

See docs/mmmu_question_catalog.md for the full mining analysis.
"""

from __future__ import annotations

from . import programs as P

# ---------------------------------------------------------------------------
# RC step response
# Facts expected: tau_s, v_C_initial, v_C_final, v_C_at_1tau
# Simulation: .tran — step input, capacitor voltage waveform
# ---------------------------------------------------------------------------

RC_STEP_RESPONSE: list[dict] = [
    {
        "id": "rc_step_tau",
        "question_type": "direct",
        "question_template": (
            "Find the time constant τ of this RC circuit. Provide your answer in milliseconds."
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
            "At the instant just after the switch is thrown (t = 0⁺), "
            "what is the capacitor voltage v_C(0⁺)?"
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
        "question_template": ("Find the steady-state capacitor voltage as t → ∞."),
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
            "What is v_C at t = 1τ (one time constant after the step)? "
            "Provide your answer in volts."
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
        "question_template": ("Is the time constant τ of this RC circuit greater than 1 ms?"),
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
# Facts expected: tau_s (=L/R), i_L_initial, i_L_final, i_L_at_1tau
# Simulation: .tran — step input, inductor current waveform
# ---------------------------------------------------------------------------

RL_STEP_RESPONSE: list[dict] = [
    {
        "id": "rl_step_tau",
        "question_type": "direct",
        "question_template": (
            "Find the time constant τ = L/R of this RL circuit. "
            "Provide your answer in milliseconds."
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
        "question_template": ("Find the magnitude of the inductor current as t → ∞."),
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
            "What is the inductor current i_L(0⁺) immediately after the switch closes?"
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
            "Find the power absorbed by the resistor at t = τ (one time constant after the step)."
        ),
        "program": [
            P.read_fact("i_L_at_1tau"),
            P.read_fact("R_load_ohm"),
            P.mul("$0", "$0"),  # i^2
            P.mul("$1", "$2"),  # i^2 * R
            P.format_numeric("$2", unit="W", precision=3),
        ],
        "answer_keys": ["i_L_at_1tau", "R_load_ohm"],
        "answer_formatter": "numeric",
    },
]

# ---------------------------------------------------------------------------
# AC phasor — RC circuit
# Facts expected: V_C_mag_V, V_C_phase_deg, V_R_mag_V, I_mag_A, Z_mag_ohm, Z_phase_deg
# Simulation: .ac at single frequency (source frequency)
# ---------------------------------------------------------------------------

AC_PHASOR_RC: list[dict] = [
    {
        "id": "phasor_vc_amplitude",
        "question_type": "direct",
        "question_template": (
            "Find the amplitude (in V) of the phasor voltage V_C in the circuit."
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
            "Find the phase of the capacitor voltage V_C. Return the angular degree."
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
            "Find the magnitude of the total impedance Z_ab of the circuit "
            "in ohms. Provide your answer rounded to 2 decimal places."
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
        "question_template": ("Find the average power (in mW) received by the resistor."),
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
        "question_template": ("Is the phase of V_C negative (lagging the source)?"),
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
# Facts expected: V_CEQ, I_CQ_mA, A_v, r_out_ohm, r_in_ohm, in_saturation
# Simulation: .op (bias) + .ac (gain/impedance)
# ---------------------------------------------------------------------------

BJT_CE_AMPLIFIER: list[dict] = [
    {
        "id": "bjt_ce_vce_q",
        "question_type": "direct",
        "question_template": (
            "Given R1 = {R1_ohm} Ω, R2 = {R2_ohm} Ω, RC = {RC_ohm} Ω, "
            "RE = {RE_ohm} Ω, VCC = {VCC_dc} V, β = {beta}, "
            "find V_CE at the quiescent operating point."
        ),
        "program": [
            P.read_fact("V_CEQ"),
            P.format_numeric("$0", unit="V", precision=2),
        ],
        "answer_keys": ["V_CEQ"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ce_ic_q",
        "question_type": "direct",
        "question_template": (
            "What is the collector current I_C at the quiescent (DC) operating point? "
            "Provide your answer in mA."
        ),
        "program": [
            P.read_fact("I_CQ_mA"),
            P.format_numeric("$0", unit="mA", precision=2),
        ],
        "answer_keys": ["I_CQ_mA"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ce_av",
        "question_type": "direct",
        "question_template": (
            "Find the small-signal voltage gain A_v = V_out / V_in "
            "of this common-emitter amplifier."
        ),
        "program": [
            P.read_fact("A_v"),
            P.format_numeric("$0", unit=None, precision=2),
        ],
        "answer_keys": ["A_v"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ce_saturation",
        "question_type": "classification",
        "question_template": ("Determine if the BJT is in saturation, active, or cut-off."),
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
            "Is V_CE greater than V_CE(sat) ≈ 0.2 V (i.e., is the transistor NOT in saturation)?"
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
# Facts expected: A_v, r_out_ohm, V_CEQ, I_EQ_mA
# ---------------------------------------------------------------------------

BJT_EMITTER_FOLLOWER: list[dict] = [
    {
        "id": "bjt_ef_rout",
        "question_type": "direct",
        "question_template": (
            "Find the output resistance r_out of this common-collector (emitter follower) amplifier. "
            "Provide your answer in ohms."
        ),
        "program": [
            P.read_fact("r_out_ohm"),
            P.format_numeric("$0", unit="Ω", precision=1),
        ],
        "answer_keys": ["r_out_ohm"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ef_av",
        "question_type": "direct",
        "question_template": (
            "What is the voltage gain A_v of this emitter follower? (Expected: close to 1.)"
        ),
        "program": [
            P.read_fact("A_v"),
            P.format_numeric("$0", unit=None, precision=4),
        ],
        "answer_keys": ["A_v"],
        "answer_formatter": "numeric",
    },
    {
        "id": "bjt_ef_gain_near_unity",
        "question_type": "comparison",
        "question_template": ("Is the voltage gain of this emitter follower greater than 0.9?"),
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
# Facts expected: V_DSQ, I_DQ_mA, A_v, A_v_bypassed
# ---------------------------------------------------------------------------

MOSFET_CS_AMPLIFIER: list[dict] = [
    {
        "id": "mosfet_cs_vds_q",
        "question_type": "direct",
        "question_template": (
            "Given the circuit values, calculate V_DS at the quiescent operating point. "
            "Provide your answer in volts, rounded to 2 decimal places."
        ),
        "program": [
            P.read_fact("V_DSQ"),
            P.format_numeric("$0", unit="V", precision=2),
        ],
        "answer_keys": ["V_DSQ"],
        "answer_formatter": "numeric",
    },
    {
        "id": "mosfet_cs_id_q",
        "question_type": "direct",
        "question_template": (
            "What is the drain current I_D at the quiescent point? Provide your answer in mA."
        ),
        "program": [
            P.read_fact("I_DQ_mA"),
            P.format_numeric("$0", unit="mA", precision=2),
        ],
        "answer_keys": ["I_DQ_mA"],
        "answer_formatter": "numeric",
    },
    {
        "id": "mosfet_cs_av",
        "question_type": "direct",
        "question_template": ("Find the voltage gain A_v with the source resistor unbypassed."),
        "program": [
            P.read_fact("A_v"),
            P.format_numeric("$0", unit=None, precision=2),
        ],
        "answer_keys": ["A_v"],
        "answer_formatter": "numeric",
    },
]

# ---------------------------------------------------------------------------
# Resistor network / Thevenin equivalent
# Facts expected: R_eq_ohm, V_th_V, R_th_ohm, V_node_V, P_source_W
# Simulation: .op with test sources
# ---------------------------------------------------------------------------

RESISTOR_NETWORK: list[dict] = [
    {
        "id": "rnet_req",
        "question_type": "direct",
        "question_template": (
            "Find the equivalent resistance R_eq as seen from the terminals. "
            "Provide your answer in ohms."
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
            "Use Thevenin's theorem. Find the open-circuit voltage V_th at terminals a-b."
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
        "question_template": ("Find the Thevenin resistance R_th at terminals a-b."),
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
        "question_template": ("Find the power (in W) supplied by the source."),
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
        "question_template": ("Is the Thevenin resistance R_th greater than 1 kΩ?"),
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
# Facts expected: A_v, V_out_dc, V_out_peak, f_3dB_hz
# Simulation: .op + .ac
# ---------------------------------------------------------------------------

OP_AMP_INVERTING: list[dict] = [
    {
        "id": "opamp_inv_av",
        "question_type": "direct",
        "question_template": (
            "Find the closed-loop voltage gain A_v = −R_f / R_in of this inverting amplifier."
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
            "For the inverting amplifier shown, determine the DC output voltage."
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
            "What is the −3 dB bandwidth of this inverting amplifier configuration?"
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
            "Is this amplifier configuration inverting, non-inverting, or a buffer?"
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
# Facts expected: f_r_hz, Q, bandwidth_hz, Z_at_resonance_ohm
# Simulation: .ac sweep
# ---------------------------------------------------------------------------

RLC_SERIES_RESONANCE: list[dict] = [
    {
        "id": "rlc_res_freq",
        "question_type": "direct",
        "question_template": (
            "Find the resonant frequency of this series RLC circuit. Provide your answer in Hz."
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
        "question_template": ("Calculate the quality factor Q of this series RLC circuit."),
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
        "question_template": ("Find the −3 dB bandwidth of this series RLC circuit."),
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
            "At resonance, the impedance of a series RLC circuit is purely resistive. "
            "Is the impedance at the measured resonant frequency within 5% of the "
            "resistance R?"
        ),
        "program": [
            P.read_fact("Z_at_resonance_ohm"),
            P.read_fact("R_ohm"),
            P.push_const(0.05),
            P.mul("$1", "0.05"),
            P.compare("<"),
            P.return_bool("$4", true_label="yes", false_label="no"),
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

# Total question count
_total = sum(len(v) for v in FUTURE_QUESTION_TEMPLATES.values())
