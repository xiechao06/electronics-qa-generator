"""Transient circuit templates — RC and RL step response.

Implements two transient topologies with PWL step sources:
    RCStepResponse, RLStepResponse
"""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, INDUCTOR_VALUES, pick_e_value


class RCStepResponse(CircuitTemplate):
    """Series RC circuit with step-input voltage source.

    R: E12 series, 1 kΩ – 100 kΩ (decades 3–5).
    C: E6 series,  10 nF – 10 μF (decades −8 to −5).
    V_step: uniform 1 – 10 V.
    Simulation: .tran for 10τ.
    """

    family = "passive"
    topology = "rc_step_response"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        r1 = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        c1 = pick_e_value(E6_VALUES, decade_min=-8, decade_max=-5, rng=rng)
        v_step = rng.uniform(1.0, 10.0)

        tau = r1 * c1
        stop_time = 10.0 * tau
        # Fine step for accurate waveform extraction
        time_step = tau / 1000.0 if tau > 0 else 1e-6

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* RC step response — transient analysis",
        )
        # PWL step: 0 V until t=1 μs, then jumps to V_step
        graph.add_voltage_source("Vin", "in", "0", pwl=f"(0 0 1e-6 0 1.000001e-6 {v_step})")
        graph.add_resistor("R1", "in", "out", r1)
        graph.add_capacitor("C1", "out", "0", c1)

        sim = SimulationConfig(
            type="tran",
            tool="Xyce",
            params={"stop_time": stop_time, "time_step": time_step},
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters={
                "R_ohm": r1,
                "C_f": c1,
                "V_step": v_step,
                "tau_s": tau,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )


class RLStepResponse(CircuitTemplate):
    """Series RL circuit with step-input voltage source.

    L: selected inductor values, 1 mH – 100 mH.
    R: E12 series, 100 Ω – 10 kΩ (decades 2–4).
    V_step: uniform 1 – 10 V.
    Simulation: .tran for 10τ.
    """

    family = "passive"
    topology = "rl_step_response"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        l1 = rng.choice(INDUCTOR_VALUES)
        r1 = pick_e_value(E12_VALUES, decade_min=2, decade_max=4, rng=rng)
        v_step = rng.uniform(1.0, 10.0)

        tau = l1 / r1 if r1 > 0 else 0.0
        stop_time = 10.0 * tau if tau > 0 else 0.01
        time_step = tau / 1000.0 if tau > 0 else 1e-6

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* RL step response — transient analysis",
        )
        graph.add_voltage_source("Vin", "in", "0", pwl=f"(0 0 1e-6 0 1.000001e-6 {v_step})")
        graph.add_resistor("R1", "in", "mid", r1)
        graph.add_inductor("L1", "mid", "0", l1)

        sim = SimulationConfig(
            type="tran",
            tool="Xyce",
            params={"stop_time": stop_time, "time_step": time_step},
        )
        netlist = graph.to_spice(sim, print_signals=["I(L1)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters={
                "R_ohm": r1,
                "L_h": l1,
                "V_step": v_step,
                "tau_s": tau,
            },
            netlist=netlist,
            simulation=sim,
            probes=["I(L1)"],
            graph=graph,
        )
