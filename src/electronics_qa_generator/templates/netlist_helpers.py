"""Netlist emission helpers.

``format_netlist`` is the legacy string-template formatter. New code should use
``electronics_qa_generator.graph.CircuitGraph.to_spice()`` instead.
"""

from __future__ import annotations

from typing import Any


def format_netlist(template: str, params: dict[str, Any]) -> str:
    """Bind parameters into a SPICE netlist template string.

    Substitutes {key} placeholders with values from params.

    .. deprecated::
        Use ``CircuitGraph`` construction + ``to_spice()`` instead.
        This function remains for backward-compatibility only.

    Example:
        >>> fmt = format_netlist(
        ...     "R1 in out {R1_val}\\n.op\\n.end",
        ...     {"R1_val": 18200}
        ... )
        >>> "18.2k" in fmt
        True
    """
    return template.format(**params)
