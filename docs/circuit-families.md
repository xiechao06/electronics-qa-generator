# Circuit families and topologies

Complete taxonomy of circuit families and topologies for the electronics Q/A benchmark. Each topology is a valid SPICE/Xyce netlist generator implementing `CircuitTemplate.sample()`.

## Legend

- **Sim type**: `.op` (operating point), `.dc` (DC sweep), `.ac` (AC frequency sweep), `.tran` (transient)
- **Phase**: `mvp` (this change), `v2` (next), `v3+` (future)
- **Difficulty**: 1 (direct values), 2 (parameter-varied), 3 (perturbed/non-ideal), 4 (composed)
- **Provenance**: families 8–11 were discovered by clustering the MMMU Electronics
  subset (`assets/mmmu_electronics_unpacked/`, 291 questions). They are the circuit
  categories most common in the benchmark that the original taxonomy under-covered.

---

## 1. Passive circuits

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Voltage divider | `.op` | 1 | **mvp** | V(out), divider ratio |
| 2 | Current divider | `.op` | 1 | v2 | I(branch), current ratio |
| 3 | Resistor ladder (3-stage) | `.op` | 2 | v2 | V at each tap, equivalent R |
| 4 | RC low-pass filter | `.ac` | 1 | **mvp** | cutoff freq, gain vs freq, phase at cutoff, behavior class |
| 5 | RC high-pass filter | `.ac` | 1 | **mvp** | cutoff freq, gain vs freq, phase at cutoff, behavior class |
| 6 | RLC band-pass filter | `.ac` | 1 | **mvp** | center freq, bandwidth, Q, behavior class |
| 7 | RLC band-stop (series LC trap) | `.ac` | 2 | v2 | notch freq, −3 dB bandwidth, Q |
| 8 | RLC resonant circuit | `.ac` | 2 | v2 | resonant freq, Q, impedance at resonance |
| 9 | Twin-T notch filter | `.ac` | 2 | v2 | notch freq, bandwidth, Q factor |
| 10 | Bridged-T notch filter | `.ac` | 2 | v2 | notch freq, bandwidth, Q factor |
| 11 | Bridge circuit (Wheatstone) | `.op` | 2 | v2 | V_ab, balance condition, sensitivity to ΔR |
| 12 | RC integrator | `.tran` | 2 | v2 | time constant, output slope, saturation time |
| 13 | RC differentiator | `.tran` | 2 | v2 | peak output, pulse width, decay rate |
| 14 | Passive LC low-pass | `.ac` | 2 | v3+ | cutoff, roll-off (−40 dB/dec), impedance matching |

**Count: 14**

---

## 2. Diode circuits

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Half-wave rectifier | `.tran` | 1 | **mvp** | peak V(out), ripple Vpp, steady-state DC |
| 2 | Full-wave bridge rectifier | `.tran` | 2 | v2 | peak V(out), ripple Vpp, PIV, diode conduction angle |
| 3 | Half-wave rectifier + filter cap | `.tran` | 2 | v2 | ripple Vpp vs C_load, DC level, diode peak current |
| 4 | Full-wave rectifier + filter cap | `.tran` | 2 | v2 | ripple Vpp vs C_load, DC level, ripple frequency |
| 5 | Zener shunt regulator | `.op` + `.dc` | 2 | v2 | V_out vs V_in, regulation %, power in Zener, line/load regulation |
| 6 | Diode clipper (series) | `.tran` | 2 | v2 | clipping level, waveform shape, conduction region |
| 7 | Diode clipper (parallel/shunt) | `.tran` | 2 | v2 | clipping level, waveform shape, symmetry |
| 8 | Diode clamper (DC restorer) | `.tran` | 2 | v3+ | DC shift amount, steady-state waveform, peak-to-peak |
| 9 | LED current-limiting circuit | `.op` | 1 | v3+ | I_LED, power in R, brightness comparison |
| 10 | Voltage multiplier (doubler) | `.tran` | 3 | v3+ | V(out) DC level, ripple, stage gain |

**Count: 10**

---

## 3. Transistor circuits (BJT + MOSFET)

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | BJT common-emitter amplifier | `.op` + `.ac` | 2 | v2 | bias point (Ic, Vce), voltage gain, bandwidth, input/output Z |
| 2 | BJT emitter follower | `.op` + `.ac` | 2 | v2 | V(out) ≈ V(in) − Vbe, gain ≈ 1, output impedance |
| 3 | BJT common-base amplifier | `.op` + `.ac` | 3 | v3+ | voltage gain, input impedance, isolation |
| 4 | BJT differential pair | `.op` + `.ac` | 3 | v2 | differential gain, CMRR, tail current, offset |
| 5 | MOSFET common-source amplifier | `.op` + `.ac` | 2 | v2 | bias point (Id, Vds), gain, bandwidth |
| 6 | MOSFET source follower | `.op` + `.ac` | 2 | v3+ | V(out) vs V(in), gain ≈ 1, output impedance |
| 7 | MOSFET switch (low-side) | `.tran` | 1 | v2 | V(out) vs V(gate), Rds(on), switching time |
| 8 | MOSFET switch (high-side) | `.tran` | 2 | v3+ | V(out) vs V(gate), body diode behavior |
| 9 | BJT current mirror | `.op` | 2 | v3+ | I_out vs I_ref, output impedance, mismatch error |
| 10 | BJT cascode amplifier | `.op` + `.ac` | 3 | v3+ | gain, bandwidth, Miller effect mitigation |
| 11 | MOSFET current mirror | `.op` | 2 | v3+ | I_out vs I_ref, channel-length modulation |

**Count: 11**

---

## 4. Op-amp circuits

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Inverting amplifier | `.op` + `.ac` | 1 | v2 | gain (−Rf/Rin), bandwidth, virtual ground |
| 2 | Non-inverting amplifier | `.op` + `.ac` | 1 | v2 | gain (1 + Rf/Rg), bandwidth, input impedance |
| 3 | Summing amplifier (inverting) | `.op` | 1 | v2 | V(out) = −Rf(V1/R1 + V2/R2) |
| 4 | Difference amplifier | `.op` | 2 | v2 | V(out) = (R2/R1)(V2 − V1), CMRR |
| 5 | Integrator | `.tran` | 2 | v2 | output slope, saturation, time-domain waveform |
| 6 | Differentiator | `.tran` | 2 | v2 | peak output, noise sensitivity, pulse response |
| 7 | Active low-pass (Sallen-Key) | `.ac` | 2 | v2 | cutoff, Q, peaking, −40 dB/dec roll-off |
| 8 | Active high-pass (Sallen-Key) | `.ac` | 2 | v3+ | cutoff, Q, peaking |
| 9 | Active band-pass (MFB) | `.ac` | 2 | v2 | center freq, bandwidth, Q, gain at center |
| 10 | State-variable filter | `.ac` | 3 | v3+ | simultaneous LP/BP/HP outputs, Q, gain per output |
| 11 | Comparator (open-loop) | `.tran` | 1 | v2 | switching threshold, hysteresis (if Schmitt), output swing |
| 12 | Schmitt trigger | `.tran` | 2 | v2 | Vth+, Vth−, hysteresis width, switching time |
| 13 | Instrumentation amplifier | `.op` + `.ac` | 3 | v3+ | differential gain from R_gain, CMRR, bandwidth |
| 14 | Voltage follower (buffer) | `.op` + `.ac` | 1 | v2 | gain = 1, bandwidth, input/output impedance |
| 15 | Precision rectifier | `.tran` | 2 | v3+ | output waveform, diode drop compensation |

**Count: 15**

---

## 5. Oscillator circuits

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Wien bridge oscillator | `.tran` | 3 | v3+ | frequency, amplitude after startup, distortion, startup time |
| 2 | Phase-shift oscillator | `.tran` | 3 | v3+ | frequency from RC, gain requirement, number of stages |
| 3 | Colpitts oscillator | `.tran` | 3 | v3+ | frequency from L/C1/C2, biasing, waveform |
| 4 | Hartley oscillator | `.tran` | 3 | v3+ | frequency from L1/L2/C, tapped inductor role |
| 5 | Crystal oscillator (Pierce) | `.tran` | 3 | v3+ | frequency (crystal-dependent), startup, stability |
| 6 | Astable multivibrator (op-amp) | `.tran` | 2 | v3+ | frequency, duty cycle, amplitude |

**Count: 6**

---

## 6. Power and regulator circuits

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Zener shunt regulator | `.op` + `.dc` | 2 | v2 | V_out regulation, line/load regulation, Zener power |
| 2 | Series pass regulator (BJT) | `.op` + `.tran` | 3 | v3+ | V_out, dropout voltage, load regulation, ripple rejection |
| 3 | Series pass regulator (MOSFET LDO) | `.op` + `.tran` | 3 | v3+ | dropout voltage, quiescent current, PSRR |
| 4 | Buck converter (open-loop) | `.tran` | 3 | v3+ | V_out = D·V_in, inductor ripple, switching node waveform |
| 5 | Boost converter (open-loop) | `.tran` | 3 | v3+ | V_out = V_in/(1−D), inductor current, diode stress |
| 6 | Linear voltage regulator (7805-style) | `.op` + `.dc` | 2 | v3+ | V_out vs V_in, dropout, load regulation, thermal |

**Count: 6**

---

## 7. Mixed and composed circuits

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Amplifier with resistive load | `.op` + `.ac` | 3 | v3+ | gain reduction under load, output swing limits |
| 2 | Filter followed by amplifier | `.ac` | 3 | v3+ | overall frequency response, which stage dominates roll-off |
| 3 | Rectifier + smoothing capacitor + load | `.tran` | 3 | v3+ | ripple vs C_load interaction, DC level |
| 4 | Regulator with varying load | `.op` + `.dc` | 3 | v3+ | load regulation curve, dropout boundary |
| 5 | Amplifier + filter cascade | `.ac` | 4 | v3+ | combined transfer function, bandwidth, stability |
| 6 | Differential pair + current mirror load | `.op` + `.ac` | 4 | v3+ | gain, CMRR, output swing, bias stability |
| 7 | Two-stage op-amp (Miller-compensated) | `.op` + `.ac` | 4 | v3+ | open-loop gain, phase margin, GBW, slew rate |

**Count: 7**

---

## 8. Resistor-network analysis (MMMU-derived)

From the MMMU "Electrical Circuit" subfield (~21 questions). Same DC circuits as
family 1, but the question focus is **network-reduction theorems and methods**
rather than a single divider ratio. SPICE establishes ground truth; the question
engine targets the analysis method.

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Series/parallel equivalent resistance | `.op` | 1 | v2 | R_eq at terminals, total source current |
| 2 | R-2R / ladder network | `.op` | 2 | v2 | tap voltages, equivalent R, current split |
| 3 | Thévenin equivalent | `.op` + `.dc` | 2 | v2 | V_th, R_th at a port |
| 4 | Norton equivalent | `.op` + `.dc` | 2 | v2 | I_N, R_N at a port |
| 5 | Superposition (multi-source) | `.op` | 3 | v2 | per-source contribution, total V/I |
| 6 | Nodal/mesh multi-source network | `.op` | 3 | v3+ | node voltages, branch currents |
| 7 | General bridge network | `.op` | 3 | v3+ | bridge current, balance condition, power delivered |

**Count: 7**

---

## 9. AC steady-state / phasor circuits (MMMU-derived)

From MMMU (~36 questions — the single largest circuit category). Single-frequency
phasor analysis: impedance, reactance, and complex V/I. Implemented as a one-point
`.ac` analysis at the source frequency.

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Series RLC impedance | `.ac` (1 freq) | 2 | v2 | \|Z\|, phase angle, phasor current |
| 2 | Parallel RLC impedance | `.ac` (1 freq) | 2 | v2 | \|Z\|, phase, resonance behavior |
| 3 | RC phasor (magnitude & phase) | `.ac` (1 freq) | 1 | v2 | V phasor magnitude, phase angle |
| 4 | RL phasor (magnitude & phase) | `.ac` (1 freq) | 1 | v2 | V/I phasor, phase angle |
| 5 | AC ladder network | `.ac` (1 freq) | 3 | v3+ | V_out magnitude & phase |
| 6 | Power factor / complex power | `.ac` (1 freq) | 2 | v3+ | real/reactive/apparent power, PF |
| 7 | Equivalent C / L network | `.op` | 1 | v2 | C_eq, L_eq at terminals |

**Count: 7**

---

## 10. RC/RL transient — step & source-free (MMMU-derived)

From MMMU (~10 questions). First- and second-order time-domain response to a step,
ramp, or switching event. Distinct from the frequency-domain filters in family 1.

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Series RC step response | `.tran` | 1 | v2 | time constant τ, v_C(t), final value |
| 2 | Series RL step response | `.tran` | 1 | v2 | time constant τ, i_L(t), final value |
| 3 | Source-free RC decay | `.tran` | 1 | v2 | decay constant, v(t) for t>0 |
| 4 | Source-free RL decay | `.tran` | 1 | v2 | decay constant, i(t) for t>0 |
| 5 | Switched network (initial conditions) | `.tran` | 3 | v3+ | v/i just after switching, steady state |
| 6 | Second-order RLC step | `.tran` | 3 | v3+ | damping (under/over/critical), overshoot, settling time |

**Count: 6**

---

## 11. Transformer / coupled circuits (MMMU-derived)

From MMMU (~4 questions). Magnetically coupled circuits.

| # | Topology | Sim | Difficulty | Phase | Key facts |
|---|---------|-----|-----------|-------|-----------|
| 1 | Ideal transformer (turns ratio) | `.op` + `.ac` | 2 | v3+ | V/I ratio, reflected impedance |
| 2 | Coupled inductors (mutual inductance) | `.ac` | 3 | v3+ | coupling coefficient k, induced voltage |

**Count: 2**

---

## Out of scope (not template-able)

The MMMU subset also contains many questions with **no SPICE-template equivalent**,
mostly from the "Signal Processing" subfield (~97 questions). These are excluded:

- Fourier series / transform of arbitrary waveforms
- Laplace transform of arbitrary waveforms
- Pure step-function / signal-decomposition problems
- Nonlinear elements defined symbolically (e.g., φ = i + tanh(i), C(t) = C₀(1 + 0.5 sin t))

These require symbolic math, not circuit simulation, and belong to a separate
non-circuit question track if ever pursued.

---

## Summary

| Family | Topologies | MVP (now) | v2 | v3+ |
|---|---|---|---|---|
| Passive | 14 | 4 | 8 | 2 |
| Diode | 10 | 1 | 7 | 2 |
| Transistor | 11 | 0 | 5 | 6 |
| Op-amp | 15 | 0 | 10 | 5 |
| Oscillator | 6 | 0 | 0 | 6 |
| Power/regulator | 6 | 0 | 1 | 5 |
| Mixed/composed | 7 | 0 | 0 | 7 |
| Resistor-network analysis *(MMMU)* | 7 | 0 | 5 | 2 |
| AC steady-state / phasor *(MMMU)* | 7 | 0 | 5 | 2 |
| RC/RL transient *(MMMU)* | 6 | 0 | 4 | 2 |
| Transformer / coupled *(MMMU)* | 2 | 0 | 0 | 2 |
| **Total** | **91** | **5** | **45** | **41** |
