## 1. Transient templates (rc_step_response, rl_step_response)

- [x] 1.1 Create `templates/transient.py` with `RCStepResponse` and `RLStepResponse` classes (sampling, PWL step source, .tran config)
- [x] 1.2 Add `_extract_rc_step` and `_extract_rl_step` to `extraction/facts.py` with registry entries
- [x] 1.3 Move RC step + RL step question templates from `future_templates.py` into `QUESTION_TEMPLATES` in `templates.py`
- [x] 1.4 Create SVG schematics `rc_step_response.svg` and `rl_step_response.svg` with fully-connected wires
- [x] 1.5 Register SVG templates in `render/svg_templates.py`
- [x] 1.6 Add `RCStepResponse`, `RLStepResponse` to `ALL_TEMPLATES` in `templates/__init__.py`

## 2. AC phasor template (ac_phasor_rc)

- [x] 2.1 Create `templates/ac_phasor.py` with `ACPhasorRC` class (single-frequency .ac config)
- [x] 2.2 Add `_extract_ac_phasor_rc` to `extraction/facts.py` with registry entry
- [x] 2.3 Move AC phasor question templates into `QUESTION_TEMPLATES`
- [x] 2.4 Create SVG schematic `ac_phasor_rc.svg` with fully-connected wires
- [x] 2.5 Register SVG template and add to `ALL_TEMPLATES`

## 3. BJT templates (bjt_ce_amplifier, bjt_emitter_follower)

- [x] 3.1 Create `templates/bjt.py` with `BJTCEAmplifier` and `BJTEFollower` classes (2N2222 model, β sampling, .op + .ac)
- [x] 3.2 Add `_extract_bjt_ce` and `_extract_bjt_ef` to `extraction/facts.py` with registry entries
- [x] 3.3 Move BJT question templates (5 CE + 3 EF) into `QUESTION_TEMPLATES`
- [x] 3.4 Create SVG schematics `bjt_ce_amplifier.svg` and `bjt_emitter_follower.svg` — fully connected, no gaps
- [x] 3.5 Register SVG templates and add to `ALL_TEMPLATES`

## 4. MOSFET template (mosfet_cs_amplifier)

- [x] 4.1 Create `templates/mosfet.py` with `MOSFETCSAmplifier` class (Level=1 NMOS, sampled VTO/KP, .op + .ac)
- [x] 4.2 Add `_extract_mosfet_cs` to `extraction/facts.py` with registry entry
- [x] 4.3 Move MOSFET CS question templates (3) into `QUESTION_TEMPLATES`
- [x] 4.4 Create SVG schematic `mosfet_cs_amplifier.svg` — fully connected
- [x] 4.5 Register SVG template and add to `ALL_TEMPLATES`

## 5. Resistor network template (resistor_network)

- [x] 5.1 Create `templates/network.py` with `ResistorNetwork` class (multi-resistor DC, test-source R_th)
- [x] 5.2 Add `_extract_resistor_network` to `extraction/facts.py` with registry entry
- [x] 5.3 Move resistor network question templates (5) into `QUESTION_TEMPLATES`
- [x] 5.4 Create SVG schematic `resistor_network.svg` — fully connected
- [x] 5.5 Register SVG template and add to `ALL_TEMPLATES`

## 6. Op-amp template (op_amp_inverting)

- [x] 6.1 Create `templates/op_amp.py` with `OpAmpInverting` class (VCVS E-element, .op + .ac)
- [x] 6.2 Add `_extract_op_amp_inverting` to `extraction/facts.py` with registry entry
- [x] 6.3 Move op-amp question templates (4) into `QUESTION_TEMPLATES`
- [x] 6.4 Create SVG schematic `op_amp_inverting.svg` — fully connected
- [x] 6.5 Register SVG template and add to `ALL_TEMPLATES`

## 7. Series RLC resonance template (rlc_series_resonance)

- [x] 7.1 Create `templates/rlc_resonance.py` with `RLCSeriesResonance` class (.ac sweep)
- [x] 7.2 Add `_extract_rlc_series_resonance` to `extraction/facts.py` with registry entry
- [x] 7.3 Move RLC resonance question templates (4) into `QUESTION_TEMPLATES`
- [x] 7.4 Create SVG schematic `rlc_series_resonance.svg` — fully connected
- [x] 7.5 Register SVG template and add to `ALL_TEMPLATES`

## 8. Integration tests and verification

- [x] 8.1 Write `tests/test_templates/test_transient.py` — verify sampling, netlist emission, Xyce convergence
- [x] 8.2 Write tests for BJT, MOSFET, op-amp, network, resonance templates
- [x] 8.3 Write `tests/test_extraction/test_future_facts.py` — verify fact extractors against cached sim output
- [x] 8.4 Run `uv run eqa questions <topology> --seed 0` for all 9 topologies — verify 38 QA items produce valid answers
- [x] 8.5 Validate all 9 SVG templates for endpoint connectivity (no solo wire endpoints at junctions)
- [x] 8.6 Run `uv run ruff check .` and `uv run pytest` — full green
