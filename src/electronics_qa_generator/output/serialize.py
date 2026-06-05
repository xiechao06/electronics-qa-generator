"""Serialize CircuitRecord to JSON-compatible dict/string.

Forward-only serialization: no deserialization from JSON back to CircuitRecord
is provided (see design.md for rationale).
"""

from __future__ import annotations

import json

from ..models import CircuitRecord


def simulation_to_dict(sim) -> dict | None:
    """Flatten a SimulationConfig into a dict, or return None."""
    if sim is None:
        return None
    return {
        "type": sim.type,
        "tool": sim.tool,
        "params": dict(sim.params),
    }


def record_to_dict(record: CircuitRecord) -> dict:
    """Convert a CircuitRecord into a JSON-compatible dict.

    Field order matches the dataclass declaration. Nested SimulationConfig
    is flattened into a dict; None simulation maps to null/None.
    """
    return {
        "id": record.id,
        "family": record.family,
        "topology": record.topology,
        "difficulty": record.difficulty,
        "parameters": dict(record.parameters),
        "netlist": record.netlist,
        "simulation": simulation_to_dict(record.simulation),
        "probes": list(record.probes),
    }


def record_to_json(record: CircuitRecord, *, indent: int = 2) -> str:
    """Serialize a CircuitRecord to a JSON string.

    The output is valid JSON parseable by json.loads. Same record + same
    indent produce byte-identical output.
    """
    return json.dumps(record_to_dict(record), indent=indent, sort_keys=False)
