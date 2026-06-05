"""SPICE/Xyce netlist emission from a CircuitGraph.

Converts a graph into a valid Xyce netlist string. Component values are
formatted with engineering-unit suffixes matching the existing
templates/netlist_helpers.py conventions.

Design: emit components in insertion order, then directives, then simulation
card, then .print line(s), then .end.
"""

from __future__ import annotations

from ..models import SimulationConfig
from .models import CircuitGraph


# -- value formatting (matches templates/netlist_helpers.py) ---------------


def _fmt_resistance(ohms: float) -> str:
    if ohms >= 1e6:
        return f"{ohms / 1e6:.4g}Meg"
    if ohms >= 1e3:
        return f"{ohms / 1e3:.4g}k"
    return f"{ohms:.4g}"


def _fmt_capacitance(farads: float) -> str:
    if farads >= 1e-3:
        return f"{farads * 1e3:.4g}m"
    if farads >= 1e-6:
        return f"{farads * 1e6:.4g}u"
    if farads >= 1e-9:
        return f"{farads * 1e9:.4g}n"
    if farads >= 1e-12:
        return f"{farads * 1e12:.4g}p"
    return f"{farads:.4g}"


def _fmt_inductance(henries: float) -> str:
    if henries >= 1:
        return f"{henries:.4g}"
    if henries >= 1e-3:
        return f"{henries * 1e3:.4g}m"
    if henries >= 1e-6:
        return f"{henries * 1e6:.4g}u"
    return f"{henries:.4g}"


def _fmt_voltage(v: float) -> str:
    if abs(v) >= 1e3:
        return f"{v / 1e3:.4g}kV"
    if abs(v) >= 1:
        return f"{v:.4g}"
    return f"{v:.4g}"


def _fmt_frequency(hz: float) -> str:
    if hz >= 1e6:
        return f"{hz / 1e6:.4g}Meg"
    if hz >= 1e3:
        return f"{hz / 1e3:.4g}k"
    return f"{hz:.4g}"


# -- component line emitters ------------------------------------------------


def _emit_resistor(c) -> str:
    return f"{c.name} {c.pos} {c.neg} {_fmt_resistance(c.params['value'])}"


def _emit_capacitor(c) -> str:
    return f"{c.name} {c.pos} {c.neg} {_fmt_capacitance(c.params['value'])}"


def _emit_inductor(c) -> str:
    return f"{c.name} {c.pos} {c.neg} {_fmt_inductance(c.params['value'])}"


def _emit_vsource(c) -> str:
    """Emit a voltage source line: Vname pos neg [DC x] [AC x] [SIN(...)]"""
    parts = [c.name, c.pos, c.neg]
    p = c.params
    if "dc" in p:
        parts.append(f"DC {_fmt_voltage(p['dc'])}")
    if "ac" in p:
        parts.append(f"AC {_fmt_voltage(p['ac'])}")
    if "sin" in p:
        s = p["sin"]
        amp = _fmt_voltage(s["amplitude"])
        freq = s["freq"]
        # Format freq without trailing .0 for integer values
        freq_str = f"{freq:.4g}"
        phase = s.get("phase", 0)
        offset = s.get("offset", 0)
        parts.append(f"SIN({offset} {amp} {freq_str} {phase} 0)")
    if "pwl" in p:
        parts.append(f"PWL{p['pwl']}")
    return " ".join(parts)


def _emit_diode(c) -> str:
    return f"{c.name} {c.pos} {c.neg} {c.params['model']}"


def _emit_bjt(c) -> str:
    """Emit a BJT: Qname collector base emitter model"""
    emitter = c.params.get("emitter", c.neg)
    return f"{c.name} {c.pos} {c.neg} {emitter} {c.params['model']}"


def _emit_mosfet(c) -> str:
    """Emit a MOSFET: Mname drain gate source bulk model"""
    source = c.params.get("source", c.neg)
    bulk = c.params.get("bulk", "0")  # bulk usually tied to source or ground
    return f"{c.name} {c.pos} {c.neg} {source} {bulk} {c.params['model']}"


_COMPONENT_EMITTERS = {
    "resistor": _emit_resistor,
    "capacitor": _emit_capacitor,
    "inductor": _emit_inductor,
    "vsource": _emit_vsource,
    "diode": _emit_diode,
    "bjt": _emit_bjt,
    "mosfet": _emit_mosfet,
}


# -- simulation card ---------------------------------------------------------


def _emit_simulation(sim: SimulationConfig) -> tuple[str, str]:
    """Return (simulation_control_card, print_card_line)."""
    sim_type = sim.type
    params = sim.params

    if sim_type == "op":
        return ".op", ".print dc"

    if sim_type == "ac":
        start = _fmt_frequency(params["start_hz"])
        stop = _fmt_frequency(params["stop_hz"])
        ppd = params["points_per_decade"]
        return f".ac dec {ppd} {start} {stop}", ".print ac"

    if sim_type == "tran":
        step = params.get("time_step")
        stop = params.get("stop_time")
        if step is not None:
            return f".tran {step:.4g} {stop:.4g}", ".print tran"
        return f".tran {stop:.4g}", ".print tran"

    if sim_type == "dc":
        source = params["source"]
        start = params["start"]
        stop = params["stop"]
        step = params["step"]
        return f".dc {source} {start} {stop} {step}", ".print dc"

    raise ValueError(f"unknown simulation type: {sim_type!r}")


# -- main emitter ------------------------------------------------------------


def emit_spice(
    graph: CircuitGraph,
    simulation: SimulationConfig,
    print_signals: list[str] | None = None,
) -> str:
    """Emit a complete Xyce netlist string from a circuit graph.

    Args:
        graph: The circuit graph to serialize.
        simulation: Simulation configuration (.op / .ac / .tran / .dc).
        print_signals: Signals to include in the .print line (e.g. ["V(out)"]).
                       Defaults to ["V(out)"] if not provided.

    Returns:
        A valid Xyce netlist string ending with ``.end\\n``.
    """
    lines: list[str] = []

    # Header comment
    if graph.header_comment is not None:
        lines.append(graph.header_comment)

    # Components (insertion order)
    for comp in graph.components:
        emitter = _COMPONENT_EMITTERS.get(comp.kind)
        if emitter is None:
            raise ValueError(f"unknown component kind: {comp.kind!r}")
        line = emitter(comp)
        if comp.comment:
            line = f"{comp.comment}\n{line}"
        lines.append(line)

    # Directives (e.g. .model)
    for directive in graph.directives:
        lines.append(directive)

    # Simulation control card
    sim_card, print_prefix = _emit_simulation(simulation)
    lines.append(sim_card)

    # .print line
    signals = print_signals if print_signals else ["V(out)"]
    lines.append(f"{print_prefix} {' '.join(signals)}")

    # End
    lines.append(".end")

    return "\n".join(lines)
