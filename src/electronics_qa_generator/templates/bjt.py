"""BJT circuit templates — common-emitter amplifier and emitter follower."""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, pick_e_value, snap_e_value

# 2N2222 NPN BJT model (standard SPICE parameters). Bf (forward beta) is
# injected per sample so the simulated device actually uses the beta the
# question states — otherwise the stated beta would be fiction and the
# simulation (the source of truth) would silently use a different value.
_BJT_MODEL_TEMPLATE = (
    ".model Q2N2222 NPN (Is=14.34f Xti=3 Eg=1.11 Vaf=74.03 Bf={beta} Ne=1.307 "
    "Ise=14.34f Ikf=.2847 Xtb=1.5 Br=6.092 Nc=2 Isc=0 Ikr=0 Rc=1 "
    "Cjc=7.306p Mjc=.3416 Vjc=.75 Fc=.5 Cje=22.01p Mje=.377 Vje=.75 "
    "Tr=46.91n Tf=411.1p Itf=.6 Vtf=1.7 Xtf=3 Rb=10)"
)


def _bjt_model(beta: float) -> str:
    """Return the 2N2222 model string with forward beta set to *beta*."""
    return _BJT_MODEL_TEMPLATE.format(beta=beta)


_BETA_VALUES = [100, 150, 200, 300]


class BJTCEAmplifier(CircuitTemplate):
    """Self-biased BJT common-emitter amplifier.

    The bias network is *designed* from a target quiescent point so the
    transistor lands in the forward-active region (where a common-emitter
    "amplifier" actually amplifies) rather than being sampled blindly, which
    frequently drove the device into saturation. Diversity comes from the
    sampled VCC, target collector current, headroom split, and β, plus E12
    rounding of the designed resistors. Simulation remains the source of truth
    for the realised operating point.

    VCC: uniform 9 - 20 V.
    I_C target: uniform 0.5 - 3 mA.
    R1, R2: voltage-divider bias designed for a stiff divider (I_div ≈ 10·I_B).
    RC: sized so the collector drop is 30-45% of VCC.
    RE: sized so the emitter sits at 10-15% of VCC.
    β: sampled from {100, 150, 200, 300}.
    Simulation: .ac (gain) + a .dc operating-point pass (bias facts).
    """

    family = "transistor"
    topology = "bjt_ce_amplifier"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        vcc = rng.uniform(9.0, 20.0)
        beta = rng.choice(_BETA_VALUES)
        i_c = rng.uniform(0.5e-3, 3.0e-3)

        # Headroom split: emitter at ~10-15% of VCC, collector drop 30-45%.
        gamma = rng.uniform(0.10, 0.15)  # V_E / VCC
        alpha = rng.uniform(0.30, 0.45)  # I_C * RC / VCC
        v_e = gamma * vcc
        v_b = v_e + 0.7

        # Emitter and collector resistors from the target current.
        re = snap_e_value(v_e / i_c, E12_VALUES)
        rc = snap_e_value(alpha * vcc / i_c, E12_VALUES)

        # Stiff voltage divider: bleeder current ~10x base current so V_B is
        # set by the divider, not loaded down by the base.
        i_b = i_c / beta
        i_div = 10.0 * i_b
        r2 = snap_e_value(v_b / i_div, E12_VALUES)
        r1 = snap_e_value((vcc - v_b) / (i_div + i_b), E12_VALUES)

        # Bypass capacitor for RE
        c_bypass = pick_e_value(E6_VALUES, decade_min=-6, decade_max=-5, rng=rng)
        # Coupling capacitors
        c_in = pick_e_value(E6_VALUES, decade_min=-6, decade_max=-5, rng=rng)
        c_out = pick_e_value(E6_VALUES, decade_min=-6, decade_max=-5, rng=rng)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment=f"* BJT CE amplifier — β={beta}",
        )
        # Supply
        graph.add_voltage_source("VCC", "vcc", "0", dc=vcc)
        # Input coupling
        graph.add_voltage_source("Vin", "in", "0", ac=1)
        graph.add_capacitor("Cin", "in", "base", c_in)
        # Bias network
        graph.add_resistor("R1", "vcc", "base", r1)
        graph.add_resistor("R2", "base", "0", r2)
        # BJT (Q1) — collector, base, emitter
        graph.add_resistor("RC", "vcc", "collector", rc)
        graph.add_bjt("Q1", "collector", "base", "emitter", model="Q2N2222")
        graph.add_resistor("RE", "emitter", "0", re)
        graph.add_capacitor("Cbypass", "emitter", "0", c_bypass)
        # Output coupling
        graph.add_capacitor("Cout", "collector", "out", c_out)
        graph.add_resistor("Rload", "out", "0", rc * 10)
        # Model
        graph.add_directive(_bjt_model(beta))

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
                "R1_ohm": r1,
                "R2_ohm": r2,
                "RC_ohm": rc,
                "RE_ohm": re,
                "VCC_dc": vcc,
                "beta": beta,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )


class BJTEFollower(CircuitTemplate):
    """BJT emitter follower (common-collector).

    Like the CE stage, the divider is designed for a forward-active quiescent
    point (emitter near mid-rail) so the follower operates correctly instead of
    bottoming out. Simulation provides the realised bias facts.

    VCC: uniform 5 - 15 V.
    I_E target: uniform 0.5 - 3 mA.
    R1, R2: stiff voltage-divider bias (emitter at ~45% of VCC).
    RE: sized from the target emitter current.
    β: sampled from {100, 150, 200, 300}.
    Simulation: .ac + a .dc operating-point pass.
    """

    family = "transistor"
    topology = "bjt_emitter_follower"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        vcc = rng.uniform(5.0, 15.0)
        beta = rng.choice(_BETA_VALUES)
        i_e = rng.uniform(0.5e-3, 3.0e-3)

        # Emitter biased near mid-rail for symmetric swing.
        v_e = rng.uniform(0.4, 0.5) * vcc
        v_b = v_e + 0.7
        re = snap_e_value(v_e / i_e, E12_VALUES)

        # Stiff divider (bleeder ~10x base current).
        i_b = i_e / (beta + 1)
        i_div = 10.0 * i_b
        r2 = snap_e_value(v_b / i_div, E12_VALUES)
        r1 = snap_e_value((vcc - v_b) / (i_div + i_b), E12_VALUES)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment=f"* BJT emitter follower — β={beta}",
        )
        graph.add_voltage_source("VCC", "vcc", "0", dc=vcc)
        graph.add_voltage_source("Vin", "in", "0", ac=1)
        # Input coupling
        c_in = pick_e_value(E6_VALUES, decade_min=-6, decade_max=-5, rng=rng)
        graph.add_capacitor("Cin", "in", "base", c_in)
        graph.add_resistor("R1", "vcc", "base", r1)
        graph.add_resistor("R2", "base", "0", r2)
        graph.add_resistor("RE", "emitter", "0", re)
        graph.add_bjt("Q1", "vcc", "base", "emitter", model="Q2N2222")
        # Output at emitter
        c_out = pick_e_value(E6_VALUES, decade_min=-6, decade_max=-5, rng=rng)
        graph.add_capacitor("Cout", "emitter", "out", c_out)
        graph.add_resistor("Rload", "out", "0", re * 10)
        graph.add_directive(_bjt_model(beta))

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
                "R1_ohm": r1,
                "R2_ohm": r2,
                "RE_ohm": re,
                "VCC_dc": vcc,
                "beta": beta,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )
