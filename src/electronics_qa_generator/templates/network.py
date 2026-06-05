"""Resistor network circuit templates."""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, pick_e_value


class ResistorNetwork(CircuitTemplate):
    """Multi-resistor DC network with Thevenin equivalent extraction.

    Constructs a bridge-like network with 4–6 resistors and one voltage source.
    Two test simulations: .op for operating point, then .op with test
    current source at terminals a-b for R_th measurement.
    """

    family = "passive"
    topology = "resistor_network"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        vsource = rng.uniform(5.0, 30.0)
        r_a = pick_e_value(E12_VALUES, decade_min=2, decade_max=5, rng=rng)
        r_b = pick_e_value(E12_VALUES, decade_min=2, decade_max=5, rng=rng)
        r_c = pick_e_value(E12_VALUES, decade_min=2, decade_max=5, rng=rng)
        r_d = pick_e_value(E12_VALUES, decade_min=2, decade_max=5, rng=rng)
        r_load = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* Resistor network — Thevenin equivalent",
        )
        # Source
        graph.add_voltage_source("Vs", "in", "0", dc=vsource)
        # Bridge: R_a from in to n1, R_b from n1 to out
        graph.add_resistor("Ra", "in", "n1", r_a)
        graph.add_resistor("Rb", "n1", "out", r_b)
        # R_c from out to n2, R_d from n2 to 0
        graph.add_resistor("Rc", "out", "n2", r_c)
        graph.add_resistor("Rd", "n2", "0", r_d)
        # Load resistor at terminals a-b (= out to 0)
        graph.add_resistor("Rload", "out", "0", r_load)

        sim = SimulationConfig(type="op", tool="Xyce")
        netlist = graph.to_spice(sim, print_signals=["V(out)", "I(Vs)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters={
                "Ra_ohm": r_a,
                "Rb_ohm": r_b,
                "Rc_ohm": r_c,
                "Rd_ohm": r_d,
                "Rload_ohm": r_load,
                "Vs_dc": vsource,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)", "I(Vs)"],
            graph=graph,
        )
