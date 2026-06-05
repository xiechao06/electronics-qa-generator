"""BJT circuit templates — common-emitter amplifier and emitter follower."""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, pick_e_value

# 2N2222 NPN BJT model (standard SPICE parameters)
_BJT_MODEL = (
    ".model Q2N2222 NPN (Is=14.34f Xti=3 Eg=1.11 Vaf=74.03 Bf=255.9 Ne=1.307 "
    "Ise=14.34f Ikf=.2847 Xtb=1.5 Br=6.092 Nc=2 Isc=0 Ikr=0 Rc=1 "
    "Cjc=7.306p Mjc=.3416 Vjc=.75 Fc=.5 Cje=22.01p Mje=.377 Vje=.75 "
    "Tr=46.91n Tf=411.1p Itf=.6 Vtf=1.7 Xtf=3 Rb=10)"
)

_BETA_VALUES = [100, 150, 200, 300]


class BJTCEAmplifier(CircuitTemplate):
    """Self-biased BJT common-emitter amplifier.

    VCC: uniform 9 – 20 V.
    R1, R2, RC, RE: E12 series (R1/R2: decades 3–5 for bias,
      RC/RE: decades 2–4).
    β: sampled from {100, 150, 200, 300}.
    Simulation: .op (bias) + .ac (small-signal gain).
    """

    family = "transistor"
    topology = "bjt_ce_amplifier"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        vcc = rng.uniform(9.0, 20.0)
        r1 = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        r2 = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        rc = pick_e_value(E12_VALUES, decade_min=2, decade_max=4, rng=rng)
        re = pick_e_value(E12_VALUES, decade_min=2, decade_max=3, rng=rng)
        beta = rng.choice(_BETA_VALUES)
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
        graph.add_directive(_BJT_MODEL)

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

    VCC: uniform 5 – 15 V.
    R1, R2: bias divider (decades 3–5).
    RE: emitter resistor (decades 2–3).
    β: sampled from {100, 150, 200, 300}.
    Simulation: .op + .ac.
    """

    family = "transistor"
    topology = "bjt_emitter_follower"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        vcc = rng.uniform(5.0, 15.0)
        r1 = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        r2 = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        re = pick_e_value(E12_VALUES, decade_min=2, decade_max=3, rng=rng)
        beta = rng.choice(_BETA_VALUES)

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
        graph.add_directive(_BJT_MODEL)

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
