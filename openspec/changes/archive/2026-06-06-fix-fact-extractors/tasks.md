## 1. Implement extractors

- [x] 1.1 ac_phasor_rc: extract V_C_mag_V, V_C_phase_deg, Z_mag_ohm, Z_phase_deg, P_avg_mW from AC sweep
- [x] 1.2 resistor_network: extract V_th_V, R_eq_ohm, P_source_W from .op data
- [x] 1.3 rlc_series_resonance: extract f_r_hz, Q, bandwidth_hz, Z_at_resonance_ohm from AC sweep data
- [x] 1.4 bjt_ce_amplifier: extract V_CEQ, I_CQ_mA, A_v, operating_region from .op+.ac
- [x] 1.5 bjt_emitter_follower: extract r_out_ohm, A_v, V_CEQ from .op+.ac
- [x] 1.6 mosfet_cs_amplifier: extract V_DSQ, I_DQ_mA, A_v from .op+.ac
- [x] 1.7 op_amp_inverting: extract A_v, V_out_dc, f_3dB_hz from .ac sweep

## 2. Verify

- [x] 2.1 Regenerate QA pairs for all 7 topologies, verify non-zero answers
- [x] 2.2 Run full test suite
