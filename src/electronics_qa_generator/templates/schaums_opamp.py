"""Op-amp inverting amplifier with feedback-to-input-node resistor.

Enriched from Schaum's Problem 6.41 (Fig. 6-37).

Topology:
  Vs → R1(2kΩ) → node_1 → R2(4kΩ) → GND      (input voltage divider shunt)
  node_1 → R3(6kΩ) → inv (-)                   (input to inverting terminal)
  node_1 ← Rf1(8kΩ) ← out                      (feedback from output to input node)
  out ← Rf2(12kΩ) → inv (-)                     (standard inverting feedback)
  (+) non-inverting terminal grounded
"""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, pick_e_value

# Ideal op-amp: VCVS with gain=1e6
_OPAMP_IDEAL = (
    ".subckt IDEAL_OPAMP in+ in- out\n"
    "Rin in+ in- 1000Meg\n"
    "E1 out 0 in+ in- 1e6\n"
    ".ends IDEAL_OPAMP\n"
)


class OpAmpInvInputFb(CircuitTemplate):
    """Inverting op-amp with additional feedback resistor to the input node.

    The output feeds back through both Rf2 (to the (-) terminal) AND Rf1
    (to the input voltage-divider node), creating a more complex gain equation.

    Parametric gain: Vo/Vs = -2×(Rf2/R3)×(R2||(R3+R_node1_thevenin))/(...)
    Exact formula: Vo = -(Rf2/R3) × V_node1, where V_node1 is set by the
    Thevenin equivalent with Rf1 feedback. Simpler: just read from Xyce.

    Parameterisation:
      Vs:  1–5 V DC
      R1:  1–5 kΩ (E12, input series)
      R2:  2–10 kΩ (E12, shunt to gnd)
      R3:  4–12 kΩ (E12, to inverting input)
      Rf1: 6–20 kΩ (E12, output→input node feedback)
      Rf2: 8–30 kΩ (E12, output→inv feedback)
    """

    family = "opamp"
    topology = "op_amp_inv_input_fb"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        vs = round(rng.uniform(1.0, 5.0), 2)
        r1 = pick_e_value(E12_VALUES, decade_min=3, decade_max=4, rng=rng)  # 1–10 kΩ
        r2 = pick_e_value(E12_VALUES, decade_min=3, decade_max=4, rng=rng)
        r3 = pick_e_value(E12_VALUES, decade_min=3, decade_max=4, rng=rng)
        rf1 = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)
        rf2 = pick_e_value(E12_VALUES, decade_min=3, decade_max=5, rng=rng)

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* Op-amp inverting amplifier with input-node feedback (Schaum's Fig. 6-37)",
        )

        graph.add_voltage_source("Vs", "in", "0", dc=vs)
        graph.add_resistor("R1", "in", "n1", r1)
        graph.add_resistor("R2", "n1", "0", r2)
        graph.add_resistor("R3", "n1", "inv", r3)
        graph.add_resistor("Rf1", "n1", "out", rf1)  # output → input node
        graph.add_resistor("Rf2", "out", "inv", rf2)  # output → (-) terminal
        graph.add_directive(_OPAMP_IDEAL)
        graph.add_directive("X1 0 inv out IDEAL_OPAMP")  # (+) = gnd

        sim = SimulationConfig(
            type="op",
            tool="Xyce",
            params={},
        )
        netlist = graph.to_spice(sim, print_signals=["V(out)"])

        params = {
            "Vs": vs,
            "R1": r1,
            "R2": r2,
            "R3": r3,
            "Rf1": rf1,
            "Rf2": rf2,
        }

        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters=params,
            graph=graph,
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
        )
