# MMMU Electronics Question Template Catalog

Mined from `assets/mmmu_electronics_unpacked/` — 194 circuit-related questions
(291 total minus 97 Signal Processing questions excluded as non-circuit).

Each entry shows: **circuit family**, **question pattern**, **MMMU source phrasing**,
**simulation facts needed**, and **how to ground the answer in Xyce output**.

---

## Mining methodology

All 194 questions were clustered by:
- **Circuit type** (BJT, MOSFET, RC/RL, AC phasor, network theorems, power, diode, op-amp)
- **Target quantity** (V_out, I_C, τ, Z_ab, A_v, P_avg, f_resonant, …)
- **Question verb** (find, calculate, determine, evaluate, use Thevenin's / superposition)
- **Answer format** (open numeric, multiple-choice, complex number, expression)

---

## 1. Voltage divider / DC resistor circuit
*Existing template family: `voltage_divider`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Direct Vout | "Find the DC output voltage." | `Vout_dc` from `.op` |
| Ratio | "Calculate the voltage divider ratio Vout/Vin." | `Vout_dc / Vin_dc` |
| Power in R | "Find the power supplied by the source." | `P = Vin * I = Vin^2 / (R1+R2)` |
| Node voltage | "With R = X, find the power supplied by the Y-V source." | computed from `.op` V/I |

---

## 2. RC low-pass / high-pass filter
*Existing template family: `rc_lowpass`, `rc_highpass`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Cutoff freq | "Find the −3 dB cutoff frequency." | `cutoff_hz` from `.ac` |
| With formula | "The theoretical cutoff is fc = 1/(2πRC). With R = {R} and C = {C}, calculate fc." | `cutoff_hz` |
| Passband gain | "What is the passband gain in dB?" | `passband_gain_db` |
| Behavior class | "Is this a low-pass or high-pass filter?" | `behavior` |
| Above/below ref | "Is the cutoff frequency above 1 kHz?" | `cutoff_hz > 1000` |

---

## 3. RLC band-pass filter
*Existing template family: `rlc_bandpass`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Center freq | "Find the center (resonant) frequency." | `center_freq_hz` |
| Bandwidth | "What is the −3 dB bandwidth?" | `bandwidth_hz` |
| Q factor | "Calculate the quality factor Q = fc / BW." | `Q` derived |
| Selectivity | "Is the bandwidth less than 10% of the center frequency?" | comparison |

---

## 4. Half-wave rectifier
*Existing template family: `half_wave_rectifier`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| DC output | "Calculate the average (DC) output voltage." | `Vout_dc` |
| Peak Vout | "What is the peak output voltage?" | `Vout_peak` |
| Ripple ratio | "Calculate the ripple ratio (ripple_vpp / Vout_dc)." | derived |
| Ripple in mV | "What is the peak-to-peak ripple in millivolts?" | `ripple_vpp * 1000` |
| PRV rating | "Determine a safe PRV rating for this rectifier." | `Vout_peak * 2` ≈ `2 * Vin_amplitude` |
| Exceeds threshold | "Does the ripple exceed 10% of the DC output?" | comparison |

---

## 5. RC step response (transient)
*Future template family: `rc_step_response`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Time constant | "Find the time constant τ for this RC circuit." | `tau = R * C` from `.tran` decay |
| Initial voltage | "Find v_C at t = 0+ (just after the switch is thrown)." | `v_C_initial` from `.tran` |
| Final value | "Find the steady-state capacitor voltage as t → ∞." | `v_C_final` from `.tran` |
| Value at time T | "Find v_C at t = {T} ms." | interpolated from `.tran` |
| Source-free decay | "After t = 0, the circuit is source-free. Find v(t) for t > 0." | `v_C_initial * exp(-t/tau)` |
| Step response | "For the circuit shown, find v_C(t) for t > 0 in terms of V." | `v_C_final*(1-exp(-t/tau)) + v_C_initial*exp(-t/tau)` |

---

## 6. RL step response (transient)
*Future template family: `rl_step_response`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Time constant | "Find the time constant τ = L/R." | `tau = L / R` |
| Inductor current | "Find i_L(t) for t > 0." | `i_L_final*(1-exp(-t/tau))` |
| At t → ∞ | "Find the magnitude of the inductor current as t → ∞." | `i_L_final` |
| At t = 0+ | "Find i_L(0+) immediately after the switch closes." | `i_L_initial` |
| Power absorbed | "At t = {T} ms, find the power absorbed by the resistor." | `I^2 * R` at given time |

---

## 7. AC steady-state / phasor
*Future template family: `ac_phasor_rc`, `ac_phasor_rl`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Phasor magnitude | "Find the amplitude (in V) of the phasor voltage V_C." | `|V_C|` from `.ac` at ω |
| Phasor phase | "Find the phase of V_out. Return the angular degree." | `∠V_out` from `.ac` at ω |
| Complex current | "Calculate the current I_1. Provide your answer as a complex number." | `I = V/Z` |
| Total impedance | "Calculate the total impedance Z_ab. Provide your answer as a complex number." | `|Z|∠θ` from `.ac` |
| Steady-state v(t) | "Find the steady-state voltage v_c(t) = X cos(ωt + φ)." | magnitude + phase from `.ac` |
| Average power | "Find the average power (in mW) received by the resistor." | `P = 0.5 * |V|^2 / R * cos(θ)` |

---

## 8. BJT common-emitter amplifier
*Future template family: `bjt_ce_amplifier`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Quiescent V_CE | "Find V_CE at the quiescent (DC) operating point." | `V_CEQ` from `.op` |
| Quiescent I_C | "What is the collector current I_C at the Q-point?" | `I_CQ` from `.op` |
| Voltage gain | "Find the voltage gain A_v of this common-emitter amplifier." | `A_v` from `.ac` |
| Is in saturation | "Determine if the BJT is in saturation." | `V_CE < V_CE_sat` → yes/no |
| Saturation current | "Find the collector saturation current I_C(sat)." | `I_C_sat = (VCC - V_CE_sat) / R_C` |
| Bias resistor | "Given V_CQ = X V, find the required R1." | derived from Q-point equations |

---

## 9. BJT emitter follower (common-collector)
*Future template family: `bjt_emitter_follower`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Output resistance | "For the common-collector amplifier, find r_out." | `r_out` from `.ac` small-signal |
| Voltage gain | "What is the voltage gain? (Should be close to 1.)" | `A_v = V_out / V_in` from `.ac` |
| V_CE | "Find V_CE at the quiescent point." | `V_CEQ` from `.op` |

---

## 10. MOSFET common-source amplifier
*Future template family: `mosfet_cs_amplifier`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Quiescent V_DS | "Calculate V_DS at the quiescent (DC) operating point." | `V_DSQ` from `.op` |
| Drain current | "Find the drain current I_D at the Q-point." | `I_DQ` from `.op` |
| Voltage gain | "Find the voltage gain with R_S unbypassed." | `A_v` from `.ac` |
| Gain bypassed | "What is the voltage gain with source resistor bypassed?" | `A_v_bypassed` |

---

## 11. Resistor network / Thevenin
*Future template family: `resistor_network`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Equivalent R | "Find the equivalent resistance R_eq as seen from terminals a-b." | `R_eq` from `.op` (Vtest/Itest) |
| Equivalent C | "Find the equivalent capacitor C_eq." | `C_eq` from series/parallel |
| Thevenin V_th | "Use Thevenin's theorem to calculate V_th." | `V_oc` from `.op` |
| Thevenin R_th | "Find the Thevenin resistance R_th." | `R_th` = V_oc / I_sc |
| Superposition | "Use superposition to find v_x." | sum of individual source contributions |
| Node voltage | "Using nodal analysis, find v_x." | `V_node` from `.op` |
| Power from source | "Find the power supplied by the 6-V source." | `P = V * I` from `.op` |

---

## 12. Op-amp inverting / non-inverting
*Future template family: `op_amp_inverting`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Voltage gain | "Find the voltage gain A_v = -R_f / R_in." | `A_v` from `.op` or `.ac` |
| Output voltage | "Determine the DC output voltage." | `V_out` from `.op` |
| Oscillation freq | "Find the frequency of the output of this multivibrator." | `f` from `.tran` (period counting) |
| Pulse width | "Calculate τ (in ms) for the one-shot." | time constant from `.tran` |

---

## 13. Series RLC / resonance
*Future template family: `rlc_series_resonance`*

| Pattern | MMMU phrasing | Grounding fact |
|---|---|---|
| Resonant freq | "Find the resonant frequency of this series RLC circuit." | `f_r = 1/(2π√LC)` |
| Q factor | "Calculate the quality factor Q." | `Q = ω_r * L / R` |
| Bandwidth | "Find the −3 dB bandwidth." | `BW = R / (2πL)` |
| Impedance at f_r | "What is the impedance at resonance?" | `Z = R` (purely resistive) |

---

## 14. Question format patterns (language)

These are cross-cutting MMMU phrasing conventions to adopt:

| Format | Example from MMMU | Template |
|---|---|---|
| In-terms-of unit | "in terms of A", "in terms of V" | "Provide your answer in {unit}." |
| Complex number | "Provide your answer as a complex number (like 0.2 + j0.4)." | For phasor answers |
| Round to N places | "Round to 2 decimal places." | "Round to {N} decimal places." |
| Angular degree | "Return the angular degree." | For phase angle answers |
| Nearest integer | "Provide your answer in Hz, rounded to the nearest integer." | For frequency |
| At t = X | "Find v at t = 5π/3 ms." | Specific time query |
| Just after switch | "At the instant just after the switch is thrown, find v." | Initial condition |
| As t → ∞ | "Find the magnitude of the inductor current as t → ∞." | Steady-state |
| With given values | "Given R1 = X, R2 = Y, find Z." | Explicit parameter statement |
| In-circuit reference | "In the circuit shown, find..." | Standard MMMU lead-in |
| For t > 0 | "Find i_L(t) for t > 0." | Transient response expression |

---

## Summary counts

| Circuit family | Questions in MMMU | Status | Future template key |
|---|---|---|---|
| Voltage divider | ~10 | ✅ implemented | `voltage_divider` |
| RC low-pass / high-pass | ~5 | ✅ implemented | `rc_lowpass`, `rc_highpass` |
| RLC band-pass | ~5 | ✅ implemented | `rlc_bandpass` |
| Half-wave rectifier | ~5 | ✅ implemented | `half_wave_rectifier` |
| RC/RL transient step | ~50 | 🔲 future | `rc_step_response`, `rl_step_response` |
| AC phasor / steady-state | ~25 | 🔲 future | `ac_phasor_rc`, `ac_phasor_rl` |
| BJT CE amplifier | ~15 | 🔲 future | `bjt_ce_amplifier` |
| BJT emitter follower | ~5 | 🔲 future | `bjt_emitter_follower` |
| MOSFET CS amplifier | ~5 | 🔲 future | `mosfet_cs_amplifier` |
| Resistor network / Thevenin | ~20 | 🔲 future | `resistor_network` |
| Op-amp / multivibrator | ~10 | 🔲 future | `op_amp_inverting` |
| Series RLC resonance | ~5 | 🔲 future | `rlc_series_resonance` |
| Power analysis | ~19 | 🔲 future | (cross-cutting) |
