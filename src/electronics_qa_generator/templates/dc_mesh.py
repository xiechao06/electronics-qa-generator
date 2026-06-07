"""DC multi-source series mesh — enriched from Schaum's Prob. 3.60 (Fig. 3-27).

A single-loop DC circuit with two voltage sources aiding, one opposing, and
one aiding on the return path, with four resistors. Asks for the open-circuit
voltage Vab between two labelled terminals.

Topology (clockwise from V1+):
  gnd → V1(+) → n1 → R1 → a [terminal] → R2 → nc → V2(opposing) → nd
       → R3 → ne → V3(aiding return) → b [terminal] → V4(aiding) → nf → R4 → gnd

V_ab = V(a) - V(b)
     = V1 + V4 + V3 - (R1+R4)*I   where I = (V1 - V2 + V3 + V4) / (R_total)
"""

from __future__ import annotations


from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate


class DCMultisourceMesh(CircuitTemplate):
    """Single-loop DC mesh with 4 sources and 4 resistors.

    Parameterization:
      V1: 15–25 V (main source, aiding)
      V2: 20–35 V (opposing)
      V3: 10–20 V (aiding, return path)
      V4:  8–15 V (aiding, return path)
      R1–R4: 1–5 Ω (integer, to keep academic-style values readable)
    """

    family = "passive"
    topology = "dc_multisource_mesh"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)

        v1 = round(rng.uniform(15.0, 25.0), 1)
        v2 = round(rng.uniform(20.0, 35.0), 1)
        v3 = round(rng.uniform(10.0, 20.0), 1)
        v4 = round(rng.uniform(8.0, 15.0), 1)
        r1 = float(rng.randint(1, 5))
        r2 = float(rng.randint(1, 5))
        r3 = float(rng.randint(1, 5))
        r4 = float(rng.randint(1, 5))

        graph = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* DC multi-source series mesh — Schaum's Fig. 3-27",
        )

        # Nodes: 0=gnd, n1, a, nc, nd, ne, b, nf
        # V1: + at n1, - at gnd (aiding clockwise)
        graph.add_voltage_source("V1", "n1", "0", dc=v1)
        # R1: from n1 to terminal a
        graph.add_resistor("R1", "n1", "a", r1)
        # R2: from a to nc
        graph.add_resistor("R2", "a", "nc", r2)
        # V2: + at nc, - at nd (opposing — current enters + going clockwise)
        graph.add_voltage_source("V2", "nc", "nd", dc=v2)
        # R3: from nd to ne
        graph.add_resistor("R3", "nd", "ne", r3)
        # V3: + at b, - at ne (aiding — current enters - going clockwise from ne→b)
        graph.add_voltage_source("V3", "b", "ne", dc=v3)
        # V4: + at nf, - at b (aiding — current enters - going clockwise from b→nf)
        graph.add_voltage_source("V4", "nf", "b", dc=v4)
        # R4: from nf to gnd
        graph.add_resistor("R4", "nf", "0", r4)

        sim = SimulationConfig(
            type="op",
            tool="Xyce",
            params={},
        )
        netlist = graph.to_spice(
            sim,
            print_signals=["V(a)", "V(b)"],
        )

        params = {
            "V1": v1,
            "V2": v2,
            "V3": v3,
            "V4": v4,
            "R1": r1,
            "R2": r2,
            "R3": r3,
            "R4": r4,
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
            probes=["V(a)", "V(b)"],
        )
