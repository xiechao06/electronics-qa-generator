"""Diode circuit templates.

Implements the MVP diode circuit family: HalfWaveRectifier.
"""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, pick_e_value

# Standard 1N4148 SPICE model (Philips/NXP-style parameters)
_DIODE_MODEL = ".model D1N4148 D (Is=2.52n Rs=0.568 N=1.752 Cjo=4p M=0.4 tt=20n)"


class HalfWaveRectifier(CircuitTemplate):
    """Half-wave rectifier with filter capacitor.

    R_load:   E12 series, 1 kΩ – 100 kΩ (decades 3–5).
    C_filter: E6 series,  1 μF – 100 μF (decades −6 to −4).
    Vin:      uniform 1 – 20 V amplitude, 60 Hz sinusoidal.
    Diode:    1N4148 silicon small-signal diode.
    Simulation: .tran  at least 10 source periods (~167 ms).
    """

    family = "diode"
    topology = "half_wave_rectifier"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        r_load = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        c_filter = pick_e_value(E6_VALUES, decade_min=-6, decade_max=-4, rng=rng)
        vin_amp = rng.uniform(1.0, 20.0)

        freq = 60.0
        period = 1.0 / freq
        stop_time = 20 * period  # 20 periods ≈ 333 ms
        time_step = period / 1000  # ~16.7 μs for 60 Hz

        graph = CircuitGraph(header_comment="* Half-wave rectifier with filter capacitor")
        graph.add_voltage_source(
            "Vin",
            "in",
            "0",
            sin={"amplitude": vin_amp, "freq": freq},
        )
        graph.add_diode("D1", "in", "out", model="D1N4148")
        graph.add_capacitor("C1", "out", "0", c_filter)
        graph.add_resistor("Rload", "out", "0", r_load)
        graph.add_directive(_DIODE_MODEL)

        sim = SimulationConfig(
            type="tran",
            tool="Xyce",
            params={"stop_time": stop_time, "time_step": time_step},
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)", "V(in)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=1,
            parameters={
                "R_load_ohm": r_load,
                "C_filter_f": c_filter,
                "Vin_amplitude": vin_amp,
                "Vin_frequency_hz": freq,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )
