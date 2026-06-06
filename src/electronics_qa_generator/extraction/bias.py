"""Auxiliary DC operating-point pass for active-device amplifier topologies.

The primary ``.ac`` simulation yields small-signal gain but *not* the DC bias
point. To honour the project's non-negotiable invariant — *simulation
establishes facts; code only derives answers* — the bias facts (``V_CE``,
``I_C``, ``V_DS``, ``I_D``, operating region) must come from a real DC
operating-point simulation, never from analytic active-region formulas (which
are wrong whenever the sampled bias drives the device into saturation or
cut-off).

This module runs a single ``.dc`` point at the supply rail and merges the
simulated node voltages into the parsed result dict so the fact extractors can
read them. It is a no-op for every topology that does not need a bias pass, so
it can be called unconditionally on the simulate -> parse -> extract seam.
"""

from __future__ import annotations

from ..models import CircuitRecord, SimulationConfig
from ..simulation.runner import invoke_xyce
from .parsers import parse_op

# topology -> (node names to probe, supply source instance name, supply param key)
_BIAS_SPEC: dict[str, tuple[tuple[str, ...], str, str]] = {
    "bjt_ce_amplifier": (("collector", "emitter", "base"), "VCC", "VCC_dc"),
    "bjt_emitter_follower": (("emitter", "base"), "VCC", "VCC_dc"),
    "mosfet_cs_amplifier": (("drain", "source", "gate"), "VDD", "VDD_dc"),
}


def augment_with_dc_bias(parsed: dict, record: CircuitRecord) -> dict:
    """Return *parsed* augmented with simulated DC node voltages.

    For active-device amplifier topologies a single-point ``.dc`` sweep at the
    supply rail is run; the resulting ``V(NODE)`` values are merged into a copy
    of *parsed*. For all other topologies (or when the record carries no graph)
    *parsed* is returned unchanged.
    """
    spec = _BIAS_SPEC.get(record.topology)
    if spec is None or record.graph is None:
        return parsed

    nodes, source, vkey = spec
    vcc = float(record.parameters.get(vkey, 10.0))

    sim = SimulationConfig(
        type="dc",
        tool="Xyce",
        params={"source": source, "start": vcc, "stop": vcc, "step": 1.0},
    )
    signals = [f"V({n})" for n in nodes]
    netlist = record.graph.to_spice(sim, print_signals=signals)

    try:
        stdout, _rc, converged = invoke_xyce(netlist)
    except Exception:
        return parsed
    if not converged:
        return parsed

    bias = parse_op(stdout)  # {"V(COLLECTOR)": value, ...}
    if not bias:
        return parsed

    merged = dict(parsed)
    merged.update(bias)
    return merged
