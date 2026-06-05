# Backlog

Pending work items for the electronics-qa-generator pipeline.
Items are ordered by implementation priority (highest first within each section).

---

## Future circuit topology implementations

Each item requires three deliverables to become active:
1. **`CircuitTemplate`** — sampling logic + Xyce netlist emitter in `templates/`
2. **`FACT_EXTRACTOR`** — parse simulation output into canonical facts in `extraction/facts.py`
3. **Move question templates** — from `questions/future_templates.py` into `questions/templates.py`

Question templates for all 9 topologies are already written and waiting in
`src/electronics_qa_generator/questions/future_templates.py`.
Simulation analysis is documented in `docs/mmmu_question_catalog.md`.
Circuit families are catalogued in `docs/circuit-families.md`.

---

### 1. RC step response
- **Template key:** `rc_step_response`
- **Circuit:** Series RC with step input (switch closes at t = 0)
- **Simulation:** `.tran`
- **Facts needed:** `tau_s`, `v_C_initial`, `v_C_final`, `v_C_at_1tau`
- **Questions (5):** τ in ms, v_C(0⁺), v_C(∞), v_C at 1τ, τ > 1 ms?
- **MMMU grounding:** ~50 transient questions in dataset; most common circuit category
- **Phase:** v2

---

### 2. RL step response
- **Template key:** `rl_step_response`
- **Circuit:** Series RL with step input
- **Simulation:** `.tran`
- **Facts needed:** `tau_s`, `i_L_initial`, `i_L_final`, `i_L_at_1tau`, `R_load_ohm`
- **Questions (4):** τ = L/R in ms, i_L(∞), i_L(0⁺), power at τ
- **MMMU grounding:** ~12 RL transient questions (inductor current waveform)
- **Phase:** v2

---

### 3. AC phasor — RC circuit
- **Template key:** `ac_phasor_rc`
- **Circuit:** Series RC driven by sinusoidal source at a single frequency
- **Simulation:** `.ac` (one frequency point)
- **Facts needed:** `V_C_mag_V`, `V_C_phase_deg`, `Z_mag_ohm`, `Z_phase_deg`, `P_avg_mW`
- **Questions (5):** |V_C|, ∠V_C, |Z_ab|, average power, is V_C lagging?
- **MMMU grounding:** ~25 phasor/impedance questions; "Find the amplitude of phasor V_C"
- **Phase:** v2

---

### 4. BJT common-emitter amplifier
- **Template key:** `bjt_ce_amplifier`
- **Circuit:** Self-biased BJT CE stage (R1, R2, RC, RE, bypass cap)
- **Simulation:** `.op` (bias) + `.ac` (small-signal gain)
- **Facts needed:** `V_CEQ`, `I_CQ_mA`, `A_v`, `r_out_ohm`, `operating_region`
- **Questions (5):** V_CE_Q, I_C_Q, A_v, operating region, in saturation?
- **MMMU grounding:** ~15 BJT CE questions; "Find V_CE given R1, R2, RC, RE, VCC, β"
- **Phase:** v2

---

### 5. Resistor network / Thevenin
- **Template key:** `resistor_network`
- **Circuit:** Multi-resistor DC network with voltage/current sources
- **Simulation:** `.op` with test sources for R_th measurement
- **Facts needed:** `R_eq_ohm`, `V_th_V`, `R_th_ohm`, `P_source_W`
- **Questions (5):** R_eq, V_th, R_th, power from source, R_th > 1 kΩ?
- **MMMU grounding:** ~20 network theorem questions; "Use Thevenin's theorem to calculate V_ab"
- **Phase:** v2

---

### 6. Op-amp inverting amplifier
- **Template key:** `op_amp_inverting`
- **Circuit:** Inverting op-amp with Rf, Rin, ideal op-amp model
- **Simulation:** `.op` + `.ac`
- **Facts needed:** `A_v`, `V_out_dc`, `f_3dB_hz`, `configuration`
- **Questions (4):** A_v = −Rf/Rin, V_out DC, −3 dB bandwidth, inverting/non-inverting?
- **MMMU grounding:** ~10 op-amp questions; "Find the dc output voltage"
- **Phase:** v2

---

### 7. Series RLC resonance
- **Template key:** `rlc_series_resonance`
- **Circuit:** Series RLC with AC source (frequency sweep)
- **Simulation:** `.ac`
- **Facts needed:** `f_r_hz`, `Q`, `bandwidth_hz`, `Z_at_resonance_ohm`, `R_ohm`
- **Questions (4):** f_r, Q, bandwidth, is Z purely resistive at f_r?
- **MMMU grounding:** ~5 resonance questions; closely related to `rlc_bandpass` already done
- **Phase:** v2

---

### 8. BJT emitter follower (common-collector)
- **Template key:** `bjt_emitter_follower`
- **Circuit:** NPN BJT common-collector (emitter follower)
- **Simulation:** `.op` + `.ac`
- **Facts needed:** `r_out_ohm`, `A_v`, `V_CEQ`
- **Questions (3):** r_out, A_v (≈ 1), gain > 0.9?
- **MMMU grounding:** ~5 emitter-follower questions; "Find r_out of the common-collector amplifier"
- **Phase:** v2

---

### 9. MOSFET common-source amplifier
- **Template key:** `mosfet_cs_amplifier`
- **Circuit:** NMOS CS stage (R_S, R_D, V_DD, FET parameters)
- **Simulation:** `.op` + `.ac`
- **Facts needed:** `V_DSQ`, `I_DQ_mA`, `A_v`
- **Questions (3):** V_DS_Q, I_D_Q, A_v unbypassed
- **MMMU grounding:** ~5 MOSFET questions; "Given I_DSS, V_P, R_S, find V_DS at quiescent point"
- **Phase:** v2

---

## Khan Academy enrichment

### Enrich circuit templates and question templates from Khan Academy
- **Source:** https://www.khanacademy.org/science/electrical-engineering
- **Task:** Survey the Khan Academy EE curriculum for circuit families, worked
  examples, and question patterns not yet captured by the MMMU mining.
  KA organises content into: Circuit analysis, DC circuit analysis, AC circuit
  analysis, Natural and step response, Operational amplifiers, Transistors, Diodes.
- **Deliverables:**
  - Additional question templates for the existing 5 active topologies
    (voltage divider, RC low-pass/high-pass, RLC band-pass, half-wave rectifier)
  - Additional question templates for the 9 backlog topology items (§1–9 above)
  - Any new circuit families identified but not yet in `docs/circuit-families.md`
  - Extend `docs/mmmu_question_catalog.md` with a KA-sourced patterns section
- **Why Khan Academy:** Pedagogy-first phrasing (step-by-step, clearly labelled
  quantities, consistent notation) complements the MMMU exam style. KA worked
  examples make grounding question ↔ simulation fact straightforward.
- **Status:** 🔲 pending

---

## Verifier stage

The architecture §11 reserves a Verifier that checks generated QA items for correctness
and quality. Implement as a `validation/` subpackage. Many checks can run without an
LLM — deterministic, fast, and suitable as a CI gate.

### Core invariants (already enforced)
- Answer is never sourced from LLM — `compute_answer()` runs deterministically
- Every item carries a `program` traceable to `read_fact`
- `format_numeric` couples value, unit, and tolerance at generation time

### Checks to implement

#### Static correctness (no LLM needed)

1. **Answer matches expected** — recompute answer from facts via the program and compare
   byte-for-byte with the stored answer.
2. **Parameter consistency** — verify R, C, L values in the question text match the
   sampled `record.parameters` dict.
3. **Unit consistency** — detect mismatches like question asks in kHz but answer unit
   is Hz.
4. **Answer leakage (literal)** — regex: detect when the answer string or answer_value
   appears verbatim in the question text (except classification question labels, which
   are intentional).
5. **Degenerate values** — flag items where simulation produced near-zero, NaN, or
   pathological values (cutoff_hz = 0, ripple = 0, gain = -200 dB).
6. **Tolerance appropriateness** — reject tolerances that are >50% of the answer
   magnitude for non-zero values, or tolerances that are absurdly tight (<1e-12).
7. **Question template coverage** — assert at least N question types are used per
   topology; no template produces identical questions across different seeds.

#### LLM-assisted checks (optional)

8. **Wording ambiguity** — LLM identifies vague or ambiguous phrasing ("the filter"
   when two filters exist, unspecified reference node).
9. **Semantic leakage** — LLM detects when the question implicitly reveals the answer
   through phrasing ("Given the cutoff is 233 Hz, find the bandwidth").
10. **Difficulty scoring** — LLM assigns a difficulty label based on question
    complexity (simple recall vs. multi-step derivation).

#### Visual checks (with schematic rendering)

11. **Schematic–topology match** — verify the rendered schematic PNG visually matches
    the topology named in the question.
12. **Label visibility** — check that component labels are readable in the rendered
    image (adequate contrast, non-overlapping).

### Known issues resolved

- **Voltage divider ratio bug** (fixed) — derived ratio and percentage now compute
  correctly (0.9363, 93.6%) after adding `Vin_dc` to the fact extractor's output dict.
- **Passband gain tolerance** (not a bug) — tolerance is already absolute (`0.5 ×
  10^-precision`); the assessment's "52 million%" was a relative-tolerance artifact
  from dividing 0.005 dB by −9.4e-09 dB.
- **Classification answer leakage** (fixed) — rephrased to "Classify the frequency
  response behavior of this filter." so labels don't appear in the question text.

---

## Other backlog items

### MMMU-grounded question patterns not yet coded
- **Power analysis questions** — "Find the average power received by the resistor" (19 MMMU questions)
  → requires `P_avg_W` fact from `.ac` (P = 0.5 · |V|² / R · cos θ) or `.tran` (time-average)
- **Complex-number answer format** — "Provide your answer as a complex number (like 0.2 + j0.4)"
  → phasor answers; needs a `format_complex` op in `questions/programs.py`
- **"In terms of" open answer format** — MMMU uses "in terms of A", "in terms of V"
  → already partially covered by `format_numeric` unit annotations

### Pipeline stages not yet started
- **Dataset assembler** — JSONL + Parquet output with image artifacts
- **Batch simulation orchestrator** — parallel Xyce runs with retry, timeout, deduplication

---

## Summary

| Category | Count | Status |
|---|---|---|
| Active circuit templates | 5 | ✅ done |
| Active question templates | 25 | ✅ done |
| Future circuit templates (backlog §1–9) | 9 | 🔲 pending |
| Future question templates (ready to activate) | 38 | ✅ written, pending circuits |
| MMMU patterns catalogued | 14 families, ~194 questions | ✅ `docs/mmmu_question_catalog.md` |
