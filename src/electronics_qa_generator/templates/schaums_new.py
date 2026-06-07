"""New topology templates derived from Schaum's circuit exercises.

Six topologies:
    OpAmpNoninverting     — non-inverting amplifier (Ch. 6 Fig. 6-23)
    OpAmpDifference       — difference amplifier    (Ch. 6 Fig. 6-16)
    OpAmpSumming          — summing (inverting) amplifier, 3 inputs
    DCCurrentDivider      — current source + two parallel resistors (Ch. 4 Fig. 4-8)
    ACRLSeries            — series RL single-freq phasor (Ch. 12)
    DCNodalCurrentSource  — nodal DC with voltage source + shunt R + current source (Ch. 5 Fig. 5-18)
"""

from __future__ import annotations

from ..graph.models import CircuitGraph
from ..models import CircuitRecord, SimulationConfig
from .base import CircuitTemplate
from .e_series import E12_VALUES, pick_e_value, snap_e_value

# ---------------------------------------------------------------------------
# Shared op-amp subcircuit
# ---------------------------------------------------------------------------
_OPAMP = (
    ".subckt IDEAL_OPAMP in+ in- out\n"
    "Rin in+ in- 1000Meg\n"
    "E1 out 0 in+ in- 1e6\n"
    ".ends IDEAL_OPAMP\n"
)


# ---------------------------------------------------------------------------
# 1. Non-inverting op-amp
# ---------------------------------------------------------------------------


class OpAmpNoninverting(CircuitTemplate):
    """Non-inverting amplifier (Schaum's Ch. 6, Fig. 6-23 pattern).

    Vs → Ra → nplus; Rdiv from nplus to gnd.
    V(nplus) = Vs * Rdiv/(Ra+Rdiv).
    Feedback: Rf from out→minus; Rs from minus→gnd.
    Gain = V(nplus)/Vs * (1 + Rf/Rs).
    """

    family = "opamp"
    topology = "op_amp_noninverting"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)
        vs = round(rng.uniform(1.0, 10.0), 2)
        ra = pick_e_value(E12_VALUES, decade_min=3, decade_max=4, rng=rng)
        rdiv = pick_e_value(E12_VALUES, decade_min=3, decade_max=4, rng=rng)
        rs = pick_e_value(E12_VALUES, decade_min=3, decade_max=4, rng=rng)
        rf = snap_e_value(rng.uniform(2.0, 10.0) * rs, E12_VALUES)

        # keep output below notional ±15 V rail
        vplus = vs * rdiv / (ra + rdiv)
        gain = 1 + rf / rs
        vo_est = vplus * gain
        if abs(vo_est) > 12.0:
            vs = round(12.0 / gain / (rdiv / (ra + rdiv)) * 0.8, 2)

        g = CircuitGraph(
            family=self.family, topology=self.topology, header_comment="* Non-inverting op-amp"
        )
        g.add_voltage_source("Vs", "in", "0", dc=vs)
        g.add_resistor("Ra", "in", "nplus", ra)
        g.add_resistor("Rdiv", "nplus", "0", rdiv)
        g.add_resistor("Rf", "out", "minus", rf)
        g.add_resistor("Rs", "minus", "0", rs)
        g.add_directive(_OPAMP)
        g.add_directive("X1 nplus minus out IDEAL_OPAMP")

        sim = SimulationConfig(type="op", tool="Xyce", params={})
        netlist = g.to_spice(sim, print_signals=["V(out)", "V(nplus)"])
        params = {
            "Vs": vs,
            "Ra": ra,
            "Rdiv": rdiv,
            "Rf": rf,
            "Rs": rs,
            "Ra_kohm": ra / 1000,
            "Rdiv_kohm": rdiv / 1000,
            "Rf_kohm": rf / 1000,
            "Rs_kohm": rs / 1000,
        }
        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters=params,
            graph=g,
            netlist=netlist,
            simulation=sim,
            probes=["V(out)", "V(nplus)"],
        )


# ---------------------------------------------------------------------------
# 2. Difference amplifier
# ---------------------------------------------------------------------------


class OpAmpDifference(CircuitTemplate):
    """Difference amplifier (Schaum's Ch. 6, Fig. 6-16 pattern).

    Va → Ra → minus(-); Vb → Rb → nplus(+); Rc from nplus→gnd; Rf out→minus.
    Vo = Rf/Ra * (Vb*(1+Ra/Rf)/(1+Rb/Rc) – Va)   [general]
    For matched Ra=Rb and Rf=Rc: Vo = Rf/Ra * (Vb – Va).
    """

    family = "opamp"
    topology = "op_amp_difference"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)
        va = round(rng.uniform(0.5, 8.0), 2)
        vb = round(rng.uniform(0.5, 8.0), 2)
        # Use matched resistors for predictable gain
        r_in = pick_e_value(E12_VALUES, decade_min=3, decade_max=4, rng=rng)
        rf = snap_e_value(rng.uniform(2.0, 8.0) * r_in, E12_VALUES)
        gain = rf / r_in
        # Ensure output ≤ ±12 V
        vo_est = gain * (vb - va)
        if abs(vo_est) > 11.0:
            scale = 11.0 / abs(vo_est)
            va = round(va * scale, 2)
            vb = round(vb * scale, 2)

        g = CircuitGraph(
            family=self.family, topology=self.topology, header_comment="* Difference amplifier"
        )
        g.add_voltage_source("Va", "ina", "0", dc=va)
        g.add_voltage_source("Vb", "inb", "0", dc=vb)
        g.add_resistor("Ra", "ina", "minus", r_in)  # Va → (−)
        g.add_resistor("Rb", "inb", "nplus", r_in)  # Vb → (+)
        g.add_resistor("Rc", "nplus", "0", rf)  # (+) → gnd  (matched to Rf)
        g.add_resistor("Rf", "out", "minus", rf)  # feedback
        g.add_directive(_OPAMP)
        g.add_directive("X1 nplus minus out IDEAL_OPAMP")

        sim = SimulationConfig(type="op", tool="Xyce", params={})
        netlist = g.to_spice(sim, print_signals=["V(out)"])
        params = {
            "Va": va,
            "Vb": vb,
            "Ra": r_in,
            "Rb": r_in,
            "Rc": rf,
            "Rf": rf,
            "Ra_kohm": r_in / 1000,
            "Rf_kohm": rf / 1000,
        }
        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters=params,
            graph=g,
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
        )


# ---------------------------------------------------------------------------
# 3. Summing amplifier (inverting, 3 inputs)
# ---------------------------------------------------------------------------


class OpAmpSumming(CircuitTemplate):
    """Inverting summing amplifier (Schaum's Ch. 6 pattern).

    Va→Ra→minus; Vb→Rb→minus; Vc→Rc→minus; Rf out→minus; (+) grounded.
    Vo = −Rf·(Va/Ra + Vb/Rb + Vc/Rc).
    For equal input resistors Ra=Rb=Rc=Rin: Vo = −(Rf/Rin)·(Va+Vb+Vc).
    """

    family = "opamp"
    topology = "op_amp_summing"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)
        va = round(rng.uniform(0.2, 4.0), 2)
        vb = round(rng.uniform(0.2, 4.0), 2)
        vc = round(rng.uniform(0.2, 4.0), 2)
        rin = pick_e_value(E12_VALUES, decade_min=3, decade_max=4, rng=rng)
        rf = snap_e_value(rng.uniform(1.0, 5.0) * rin, E12_VALUES)
        # Clamp so |Vo| ≤ 12 V
        gain = rf / rin
        vo_est = gain * (va + vb + vc)
        if vo_est > 11.0:
            scale = 11.0 / vo_est
            va, vb, vc = round(va * scale, 2), round(vb * scale, 2), round(vc * scale, 2)

        g = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* Summing (inverting) op-amp, 3 inputs",
        )
        g.add_voltage_source("Va", "ina", "0", dc=va)
        g.add_voltage_source("Vb", "inb", "0", dc=vb)
        g.add_voltage_source("Vc", "inc", "0", dc=vc)
        g.add_resistor("Ra", "ina", "minus", rin)
        g.add_resistor("Rb", "inb", "minus", rin)
        g.add_resistor("Rc", "inc", "minus", rin)
        g.add_resistor("Rf", "out", "minus", rf)
        g.add_directive(_OPAMP)
        g.add_directive("X1 0 minus out IDEAL_OPAMP")  # (+) = gnd

        sim = SimulationConfig(type="op", tool="Xyce", params={})
        netlist = g.to_spice(sim, print_signals=["V(out)"])
        params = {
            "Va": va,
            "Vb": vb,
            "Vc": vc,
            "Ra": rin,
            "Rb": rin,
            "Rc": rin,
            "Rf": rf,
            "Ra_kohm": rin / 1000,
            "Rf_kohm": rf / 1000,
        }
        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters=params,
            graph=g,
            netlist=netlist,
            simulation=sim,
            probes=["V(out)"],
        )


# ---------------------------------------------------------------------------
# 4. DC current divider (current source + two parallel resistors)
# ---------------------------------------------------------------------------


class DCCurrentDivider(CircuitTemplate):
    """Current source with two parallel resistors (Schaum's Ch. 4, Fig. 4-8).

    Is (upward, from gnd→v) ‖ R1 (v→gnd) ‖ R2 (v→gnd).
    V(v) = Is × (R1‖R2).
    I(R1) = V/R1, I(R2) = V/R2.
    """

    family = "passive"
    topology = "dc_current_divider"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)
        r1 = float(rng.choice([1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25]))
        r2 = float(rng.choice([1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25]))
        r_par = r1 * r2 / (r1 + r2)
        # Is such that V(v) is in a reasonable range (5–50 V)
        v_target = rng.uniform(8.0, 40.0)
        i_s = round(v_target / r_par, 3)

        g = CircuitGraph(
            family=self.family, topology=self.topology, header_comment="* DC current divider"
        )
        # Current source: upward (from gnd to v)
        g.add_current_source("Is", "0", "v", dc=i_s)
        g.add_resistor("R1", "v", "0", r1)
        g.add_resistor("R2", "v", "0", r2)

        sim = SimulationConfig(type="op", tool="Xyce", params={})
        netlist = g.to_spice(sim, print_signals=["V(v)"])
        params = {"Is": i_s, "R1": r1, "R2": r2}
        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=1,
            parameters=params,
            graph=g,
            netlist=netlist,
            simulation=sim,
            probes=["V(v)"],
        )


# ---------------------------------------------------------------------------
# 5. AC series RL (single-frequency phasor)
# ---------------------------------------------------------------------------


class ACRLSeries(CircuitTemplate):
    """Series RL circuit with a single-frequency AC source (Schaum's Ch. 12).

    Vin → R1 → nrl → L1 → gnd.
    V(nrl) = phasor voltage across the inductor.
    |V(nrl)|/Vin = ωL/√(R²+(ωL)²).
    Phase_VL relative to Vin = 90° − arctan(ωL/R).
    """

    family = "passive"
    topology = "ac_rl_series"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)
        r1 = pick_e_value(E12_VALUES, decade_min=1, decade_max=3, rng=rng)  # 10 Ω – 1 kΩ
        # Pick L so that ωL ≈ R at the chosen frequency (interesting operating point)
        freq = rng.choice([50.0, 60.0, 100.0, 500.0, 1000.0, 2000.0, 5000.0])
        omega = 2 * 3.14159265 * freq
        l_target = r1 / omega * rng.uniform(0.5, 3.0)
        # Snap to a reasonable inductor value
        from .e_series import INDUCTOR_VALUES

        l1 = min(INDUCTOR_VALUES, key=lambda v: abs(v - l_target))

        g = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* Series RL phasor (single frequency)",
            params={"freq": freq},
        )
        g.add_voltage_source("Vin", "in", "0", dc=0, ac=1)
        g.add_resistor("R1", "in", "nrl", r1)
        g.add_inductor("L1", "nrl", "0", l1)

        sim = SimulationConfig(
            type="ac",
            tool="Xyce",
            params={"start_hz": freq, "stop_hz": freq, "points_per_decade": 1},
        )
        netlist = g.to_spice(sim, print_signals=["V(nrl)"])
        params = {"R1_ohm": r1, "L1_H": l1, "freq_hz": freq, "L1_mH": l1 * 1000}
        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters=params,
            graph=g,
            netlist=netlist,
            simulation=sim,
            probes=["V(nrl)"],
        )


# ---------------------------------------------------------------------------
# 6. DC nodal: voltage source + shunt R + current source
# ---------------------------------------------------------------------------


class DCNodalCurrentSource(CircuitTemplate):
    """DC nodal circuit: Vs in series with Rs into node v; Rp shunt to gnd; Is into v.

    Schaum's Ch. 5 Fig. 5-18 pattern (parallel DC network with mixed sources).
    KCL at v: (Vs−V)/Rs = V/Rp − Is  →  V = (Vs/Rs + Is)/(1/Rs + 1/Rp).
    Questions: V(v), I through Rs, I through Rp.
    """

    family = "passive"
    topology = "dc_nodal_current_source"

    def sample(self, seed: int | None = None) -> CircuitRecord:
        rng = self._new_rng(seed)
        vs = round(rng.uniform(20.0, 120.0), 1)
        rs = float(rng.choice([1, 2, 4, 5, 8, 10, 20]))  # small series R
        rp = float(rng.choice([5, 10, 20, 25, 40, 50, 100]))  # parallel shunt
        # Is such that v stays positive and interesting
        v_no_is = vs * rp / (rs + rp)
        i_s = round(rng.uniform(-v_no_is * 0.4 / rp, v_no_is * 0.4 / rp), 2)

        g = CircuitGraph(
            family=self.family,
            topology=self.topology,
            header_comment="* DC nodal: Vs+Rs series, Rp shunt, Is current source",
        )
        g.add_voltage_source("Vs", "vsrc", "0", dc=vs)
        g.add_resistor("Rs", "vsrc", "v", rs)
        g.add_resistor("Rp", "v", "0", rp)
        # Is positive = current injected into node v (upward)
        g.add_current_source("Is", "0", "v", dc=i_s)

        sim = SimulationConfig(type="op", tool="Xyce", params={})
        netlist = g.to_spice(sim, print_signals=["V(v)"])
        params = {"Vs": vs, "Rs": rs, "Rp": rp, "Is": i_s}
        return CircuitRecord(
            id=f"{self.topology}_{seed:08x}" if seed is not None else self.topology,
            family=self.family,
            topology=self.topology,
            difficulty=2,
            parameters=params,
            graph=g,
            netlist=netlist,
            simulation=sim,
            probes=["V(v)"],
        )
