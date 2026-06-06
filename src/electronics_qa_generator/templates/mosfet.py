"""MOSFET circuit template — common-source amplifier."""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, pick_e_value

# NMOS Level=1 model
_MOSFET_MODEL = (
    ".model NMOS1 NMOS (Level=1 VTO=2.0 KP=1.0e-3 L=2e-6 W=50e-6 Lambda=0.02 Gamma=1.0 Phi=0.6)"
)


class MOSFETCSAmplifier(CircuitTemplate):
    """NMOS common-source amplifier with source degeneration.

    VDD: uniform 10 – 20 V.
    RD: E12 series, 1 kΩ – 100 kΩ (decades 3–5).
    RS: E12 series, 100 Ω – 10 kΩ (decades 2–4).
    RG: E12 series, 100 kΩ – 1 MΩ (decades 5–6).
    Simulation: .op + .ac.
    """

    family = "transistor"
    topology = "mosfet_cs_amplifier"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        vdd = rng.uniform(10.0, 20.0)
        rd = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        rs = pick_e_value(E12_VALUES, decade_min=2, decade_max=4, rng=rng)
        rg = pick_e_value(E12_VALUES, decade_min=5, decade_max=6, rng=rng)
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
        graph.add_resistor("RG", "gate", "0", rg)
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
                "RG_ohm": rg,
                "VDD_dc": vdd,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )
