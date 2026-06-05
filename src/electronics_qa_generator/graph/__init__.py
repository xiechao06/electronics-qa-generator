"""Circuit graph subpackage.

Provides a graph-centric representation of electronic circuits as an
alternative to raw SPICE strings.  CircuitGraph is the primary modeling
primitive; SPICE emission is a downstream serialization concern.

Usage::

    from electronics_qa_generator.graph import CircuitGraph, Component
    from electronics_qa_generator.models import SimulationConfig

    graph = CircuitGraph(header_comment="* My circuit")
    graph.add_voltage_source("Vin", "in", "0", dc=5.0)
    graph.add_resistor("R1", "in", "out", 1000.0)
    netlist = graph.to_spice(SimulationConfig(type="op"))
"""

from .models import CircuitGraph, Component

__all__ = ["CircuitGraph", "Component"]
