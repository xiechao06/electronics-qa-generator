"""Op-amp circuit template — inverting amplifier using ideal VCVS model."""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, pick_e_value

# Ideal op-amp: VCVS (E element) with gain=1e5, plus input/output resistances
_OPAMP_MODEL = (
    ".subckt IDEAL_OPAMP in+ in- out vcc vee\n"
    "Rin in+ in- 1Meg\n"
    "Rout mid out 75\n"
    "E1 mid 0 in+ in- 1e5\n"
    ".ends IDEAL_OPAMP\n"
)


class OpAmpInverting(CircuitTemplate):
    """Inverting amplifier using an ideal op-amp.

    Rf: E12 series, 1 kΩ – 100 kΩ (decades 3–5).
    Rin: E12 series, 1 kΩ – 100 kΩ (decades 3–5).
    Vcc: uniform ±5 – ±15 V (VCC positive, VEE negative).
    Vin_dc: uniform 0.1 – 2.0 V.
    Simulation: .op + .ac.
    """

    family = "opamp"
    topology = "op_amp_inverting"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        rf = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        rin = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        vcc_val = rng.uniform(5.0, 15.0)
        vin_dc = rng.uniform(0.1, 2.0)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* Op-amp inverting amplifier",
        )
        # Supplies
        graph.add_voltage_source("VCC", "vcc", "0", dc=vcc_val)
        graph.add_voltage_source("VEE", "vee", "0", dc=-vcc_val)
        # Input source
        graph.add_voltage_source("Vin", "in", "0", dc=vin_dc, ac=1)
        # Resistor network
        graph.add_resistor("Rin", "in", "nin", rin)
        graph.add_resistor("Rf", "nin", "out", rf)
        # Op-amp: non-inverting input to ground
        graph.add_resistor("Rgnd", "nplus", "0", 10e3)
        # Use subcircuit call for op-amp (handled as a special component)
        graph.add_directive(_OPAMP_MODEL)
        graph.add_directive("X1 nplus nin out vcc vee IDEAL_OPAMP")

        # For AC analysis, add a dominant pole cap across Rf for measurable bandwidth
        c_pole = 10e-12  # 10 pF
        graph.add_capacitor("Cpole", "nin", "out", c_pole)

        sim = SimulationConfig(
            type="ac",
            tool="Xyce",
            params={"start_hz": 1, "stop_hz": 1_000_000, "points_per_decade": 50},
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)"])

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters={
                "Rf_ohm": rf,
                "Rin_ohm": rin,
                "VCC_dc": vcc_val,
                "VEE_dc": -vcc_val,
                "Vin_dc": vin_dc,
                "A_v_theoretical": -rf / rin,
            },
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
            graph=graph,
        )
