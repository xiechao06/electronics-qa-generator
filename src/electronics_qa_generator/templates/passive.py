"""Passive circuit templates.

Implements the MVP passive circuit families:
    VoltageDivider, RCLowPass, RCHighPass, RLCBandPass

Each template constructs a CircuitGraph, calls to_spice() for netlist
emission, and returns a CircuitRecord.
"""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, INDUCTOR_VALUES, pick_e_value, snap_e_value


# ---------------------------------------------------------------------------
# 2.1 Voltage divider
# ---------------------------------------------------------------------------


class VoltageDivider(CircuitTemplate):
    """Voltage divider: two resistors in series, output at the midpoint.

    R1, R2: E12 series, 100 Ω – 1 MΩ.
    Vin:    uniform 1 – 30 V DC.
    Simulation: .op
    """

    family = "passive"
    topology = "voltage_divider"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        r1 = pick_e_value(E12_VALUES, decade_min=2, decade_max=6, rng=rng)
        r2 = pick_e_value(E12_VALUES, decade_min=2, decade_max=6, rng=rng)
        vin = rng.uniform(1.0, 30.0)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* Voltage divider — DC operating point",
        )
        graph.add_voltage_source("Vin", "in", "0", dc=vin)
        graph.add_resistor("R1", "in", "out", r1)
        graph.add_resistor("R2", "out", "0", r2)

        sim = SimulationConfig(type="op", tool="Xyce")
        netlist = graph.to_spice(sim, print_signals=["V(out)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=1,
            parameters={"R1_ohm": r1, "R2_ohm": r2, "Vin_dc": vin},
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )


# ---------------------------------------------------------------------------
# 2.2 RC low-pass filter
# ---------------------------------------------------------------------------


class RCLowPass(CircuitTemplate):
    """First-order RC low-pass filter.

    R: E12 series, 1 kΩ – 1 MΩ (decades 3–6).
    C: E6 series,  1 nF – 1 μF (decades −9 to −6).
    Simulation: .ac  sweep 0.01 Hz – 10 MHz @ 50 pts/dec.
    """

    family = "passive"
    topology = "rc_lowpass"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        r1 = pick_e_value(E12_VALUES, decade_min=3, decade_max=6, rng=rng)
        c1 = pick_e_value(E6_VALUES, decade_min=-9, decade_max=-6, rng=rng)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* RC low-pass filter",
        )
        graph.add_voltage_source("Vin", "in", "0", ac=1)
        graph.add_resistor("R1", "in", "out", r1)
        graph.add_capacitor("C1", "out", "0", c1)

        sim = SimulationConfig(
            type="ac",
            tool="Xyce",
            params={"start_hz": 0.01, "stop_hz": 10_000_000, "points_per_decade": 50},
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=1,
            parameters={"R1_ohm": r1, "C1_f": c1},
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )


# ---------------------------------------------------------------------------
# 2.3 RC high-pass filter
# ---------------------------------------------------------------------------


class RCHighPass(CircuitTemplate):
    """First-order RC high-pass filter.

    R: E12 series, 1 kΩ – 1 MΩ (decades 3–6).
    C: E6 series,  1 nF – 1 μF (decades −9 to −6).
    Simulation: .ac  sweep 0.01 Hz – 10 MHz @ 50 pts/dec.

    Topology: capacitor in series with input, resistor to ground.
    """

    family = "passive"
    topology = "rc_highpass"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        r1 = pick_e_value(E12_VALUES, decade_min=3, decade_max=6, rng=rng)
        c1 = pick_e_value(E6_VALUES, decade_min=-9, decade_max=-6, rng=rng)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* RC high-pass filter",
        )
        graph.add_voltage_source("Vin", "in", "0", ac=1)
        graph.add_capacitor("C1", "in", "out", c1)
        graph.add_resistor("R1", "out", "0", r1)

        sim = SimulationConfig(
            type="ac",
            tool="Xyce",
            params={"start_hz": 0.01, "stop_hz": 10_000_000, "points_per_decade": 50},
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=1,
            parameters={"R1_ohm": r1, "C1_f": c1},
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )


# ---------------------------------------------------------------------------
# 2.4 RLC band-pass filter
# ---------------------------------------------------------------------------


class RLCBandPass(CircuitTemplate):
    """Series RLC band-pass filter with output taken across R.

    The resistor is sized from a target quality factor Q = sqrt(L/C)/R so the
    filter has a well-defined resonant peak (Q in ~1.5-15). Sampling R, L, C
    independently produced Q from 0.003 to 30; the very low-Q seeds are
    overdamped with no real peak, so the simulated centre frequency drifts far
    from 1/(2*pi*sqrt(LC)) and f0/Q became unanswerable from the schematic.

    L: selected values,  1 mH - 100 mH.
    C: E6 series,        10 nF - 1 uF (decades -8 to -6).
    R: from Q target, snapped to E12.
    Simulation: .ac  sweep 10 Hz - 10 MHz @ 50 pts/dec.
    """

    family = "passive"
    topology = "rlc_bandpass"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        l1 = rng.choice(INDUCTOR_VALUES)
        c1 = pick_e_value(E6_VALUES, decade_min=-8, decade_max=-6, rng=rng)
        z0 = (l1 / c1) ** 0.5  # characteristic impedance sqrt(L/C)
        q_target = rng.uniform(1.5, 15.0)
        r1 = snap_e_value(z0 / q_target, E12_VALUES)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* RLC series band-pass filter  (output across R)",
        )
        graph.add_voltage_source("Vin", "in", "0", ac=1)
        graph.add_inductor("L1", "in", "mid", l1)
        graph.add_capacitor("C1", "mid", "out", c1)
        graph.add_resistor("R1", "out", "0", r1)

        sim = SimulationConfig(
            type="ac",
            tool="Xyce",
            params={"start_hz": 10, "stop_hz": 10_000_000, "points_per_decade": 500},
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=1,
            parameters={"R1_ohm": r1, "L1_h": l1, "C1_f": c1},
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )
