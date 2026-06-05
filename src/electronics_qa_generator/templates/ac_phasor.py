"""AC phasor circuit template — series RC single-frequency analysis."""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, pick_e_value


class ACPhasorRC(CircuitTemplate):
    """Series RC circuit driven by sinusoidal source at a single frequency.

    R: E12 series, 1 kΩ – 100 kΩ (decades 3–5).
    C: E6 series,  10 nF – 1 μF (decades −8 to −6).
    f_src: uniform 100 Hz – 100 kHz.
    Vin_ac: 1 V AC magnitude.
    Simulation: .ac single frequency point.
    """

    family = "passive"
    topology = "ac_phasor_rc"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        r1 = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        c1 = pick_e_value(E6_VALUES, decade_min=-8, decade_max=-6, rng=rng)
        f_src = rng.uniform(100.0, 100_000.0)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* AC phasor — series RC single-frequency",
        )
        graph.add_voltage_source("Vin", "in", "0", ac=1)
        graph.add_resistor("R1", "in", "out", r1)
        graph.add_capacitor("C1", "out", "0", c1)

        sim = SimulationConfig(
            type="ac",
            tool="Xyce",
            params={
                "start_hz": f_src,
                "stop_hz": f_src,
                "points_per_decade": 1,
            },
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)", "I(R1)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters={
                "R_ohm": r1,
                "C_f": c1,
                "f_src_hz": f_src,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )
