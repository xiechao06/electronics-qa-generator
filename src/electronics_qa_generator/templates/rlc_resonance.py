"""RLC resonance circuit template — series RLC with AC frequency sweep."""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, INDUCTOR_VALUES, pick_e_value, snap_e_value


class RLCSeriesResonance(CircuitTemplate):
    """Series RLC circuit with AC frequency sweep for resonance analysis.

    R is sized from a target quality factor Q = sqrt(L/C)/R so the circuit has a
    well-defined resonance (Q in ~2-15). Sampling R independently produced Q far
    below 1, where there is no real resonant peak and f_r/Q/BW are not
    recoverable from the schematic.

    L: selected inductor values, 1 mH - 100 mH.
    C: E6 series, 10 nF - 1 uF (decades -8 to -6).
    R: from Q target, snapped to E12.
    Simulation: .ac sweep 10 Hz - 10 MHz.
    """

    family = "passive"
    topology = "rlc_series_resonance"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        l1 = rng.choice(INDUCTOR_VALUES)
        c1 = pick_e_value(E6_VALUES, decade_min=-8, decade_max=-6, rng=rng)
        z0 = (l1 / c1) ** 0.5  # characteristic impedance sqrt(L/C)
        q_target = rng.uniform(2.0, 15.0)
        r1 = snap_e_value(z0 / q_target, E12_VALUES)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* Series RLC resonance",
        )
        graph.add_voltage_source("Vin", "in", "0", ac=1)
        graph.add_resistor("R1", "in", "mid", r1)
        graph.add_inductor("L1", "mid", "n1", l1)
        graph.add_capacitor("C1", "n1", "0", c1)

        sim = SimulationConfig(
            type="ac",
            tool="Xyce",
            params={"start_hz": 10, "stop_hz": 10_000_000, "points_per_decade": 500},
        )
        netlist = graph.to_spice(sim, print_signals=["V(mid)", "V(n1)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters={
                "R_ohm": r1,
                "L_h": l1,
                "C_f": c1,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(n1)", "I(R1)"],
            graph=graph,
        )
