"""MOSFET circuit template — common-source amplifier."""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E6_VALUES, E12_VALUES, pick_e_value, snap_e_value

# NMOS Level=1 model. Body effect (Gamma) and channel-length modulation
# (Lambda) are disabled so the simulated device obeys the ideal square law
# I_D = (KP/2)(W/L)(V_GS - VTO)^2 exactly — the same law the question states.
# Otherwise the question would inline a formula the simulator does not follow.
_MOSFET_MODEL = (
    ".model NMOS1 NMOS (Level=1 VTO=2.0 KP=1.0e-3 L=2e-6 W=50e-6 Lambda=0.0 Gamma=0.0 Phi=0.6)"
)

# Device constants implied by _MOSFET_MODEL, used only to *design* a saturation
# bias point. Simulation remains the source of truth for the realised facts.
_VTO = 2.0
_KN = 0.5 * 1.0e-3 * (50e-6 / 2e-6)  # 0.5 * KP * W/L  = 0.0125 A/V^2


class MOSFETCSAmplifier(CircuitTemplate):
    """NMOS common-source amplifier with source degeneration.

    The gate is biased by a high-impedance voltage divider (RG1 from VDD to the
    gate, RG2 from the gate to ground) and the whole bias network is *designed*
    from a target saturation operating point. The previous template tied the
    gate to ground through a single resistor, leaving V_GS = -V_S < V_TO so the
    transistor was always in cut-off and never amplified. Diversity comes from
    VDD, the target drain current, the headroom split, and E12 rounding;
    simulation provides the realised bias facts.

    VDD: uniform 10 - 20 V.
    I_D target: uniform 0.2 - 1.0 mA (saturation).
    RD: sized so the drain drop is 30-45% of VDD.
    RS: sized so the source sits at 10-20% of VDD.
    RG1, RG2: high-impedance gate divider (few MΩ) setting V_G.
    Simulation: .ac (gain) + a .dc operating-point pass (bias facts).
    """

    family = "transistor"
    topology = "mosfet_cs_amplifier"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        vdd = rng.uniform(10.0, 20.0)
        i_d = rng.uniform(0.2e-3, 1.0e-3)

        # Saturation design: V_GS = V_TO + overdrive, where I_D = k_n*V_ov^2.
        v_ov = (i_d / _KN) ** 0.5
        v_gs = _VTO + v_ov

        alpha = rng.uniform(0.30, 0.45)  # I_D * RD / VDD (drain headroom)
        beta_s = rng.uniform(0.10, 0.20)  # V_S / VDD (source degeneration)
        v_s = beta_s * vdd
        v_g = v_gs + v_s

        rd = snap_e_value(alpha * vdd / i_d, E12_VALUES)
        rs = snap_e_value(v_s / i_d, E12_VALUES)

        # High-impedance gate divider sized to set V_G = VDD * RG2/(RG1+RG2).
        rg_tot = rng.uniform(1.0e6, 5.0e6)
        ratio = v_g / vdd
        rg2 = snap_e_value(rg_tot * ratio, E12_VALUES)
        rg1 = snap_e_value(rg_tot * (1.0 - ratio), E12_VALUES)

        c_in = pick_e_value(E6_VALUES, decade_min=-6, decade_max=-5, rng=rng)
        c_out = pick_e_value(E6_VALUES, decade_min=-6, decade_max=-5, rng=rng)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* MOSFET CS amplifier",
        )
        graph.add_voltage_source("VDD", "vdd", "0", dc=vdd)
        graph.add_voltage_source("Vin", "in", "0", ac=1)
        graph.add_capacitor("Cin", "in", "gate", c_in)
        graph.add_resistor("RG1", "vdd", "gate", rg1)
        graph.add_resistor("RG2", "gate", "0", rg2)
        graph.add_resistor("RD", "vdd", "drain", rd)
        graph.add_mosfet("M1", "drain", "gate", "source", model="NMOS1")
        graph.add_resistor("RS", "source", "0", rs)
        graph.add_capacitor("Cout", "drain", "out", c_out)
        graph.add_resistor("Rload", "out", "0", rd * 10)
        graph.add_directive(_MOSFET_MODEL)

        sim = SimulationConfig(
            type="ac",
            tool="Xyce",
            params={"start_hz": 10, "stop_hz": 10_000_000, "points_per_decade": 50},
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters={
                "RD_ohm": rd,
                "RS_ohm": rs,
                "RG1_ohm": rg1,
                "RG2_ohm": rg2,
                "VDD_dc": vdd,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )
