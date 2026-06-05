"""Circuit graph data structures.

Lightweight graph representation of a circuit: nodes + ordered components.
This is the primary modeling primitive for circuit templates, separating
structure from SPICE serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import SimulationConfig


@dataclass
class Component:
    """A single circuit element with connectivity and typed parameters.

    Node names are strings (e.g. "in", "out", "0" for ground).
    Parameters store raw numeric values — formatting happens in the emitter.
    """

    name: str
    kind: str  # "resistor", "capacitor", "inductor", "vsource", "diode"
    pos: str
    neg: str
    params: dict = field(default_factory=dict)
    comment: str | None = None


@dataclass
class CircuitGraph:
    """Flat ordered-list representation of a circuit.

    Components are stored in insertion order, which determines SPICE
    netlist emission order. Nodes are tracked via a name → index map;
    node "0" is always ground.

    Templates construct graphs via the ``add_*`` methods, never by
    manipulating ``nodes`` or ``components`` directly.
    """

    nodes: dict[str, int] = field(default_factory=dict)
    components: list[Component] = field(default_factory=list)
    directives: list[str] = field(default_factory=list)
    header_comment: str | None = None

    # -- properties ------------------------------------------------------

    @property
    def node_count(self) -> int:
        """Number of non-ground nodes."""
        ground = 1 if "0" in self.nodes else 0
        return max(0, len(self.nodes) - ground)

    @property
    def component_count(self) -> int:
        """Number of components in the circuit."""
        return len(self.components)

    @property
    def non_ground_nodes(self) -> set[str]:
        """Set of node names excluding ground."""
        return set(self.nodes.keys()) - {"0"}

    def components_by_kind(self, kind: str) -> list[Component]:
        """Return all components of a given kind (e.g. "resistor")."""
        return [c for c in self.components if c.kind == kind]

    # -- construction helpers --------------------------------------------

    def _register_node(self, name: str) -> None:
        if name not in self.nodes:
            self.nodes[name] = len(self.nodes)

    def add_resistor(
        self,
        name: str,
        pos: str,
        neg: str,
        value_ohm: float,
        *,
        comment: str | None = None,
    ) -> None:
        """Add a resistor."""
        for n in (pos, neg):
            self._register_node(n)
        self.components.append(
            Component(
                name=name,
                kind="resistor",
                pos=pos,
                neg=neg,
                params={"value": value_ohm},
                comment=comment,
            ),
        )

    def add_capacitor(
        self,
        name: str,
        pos: str,
        neg: str,
        value_f: float,
        *,
        comment: str | None = None,
    ) -> None:
        """Add a capacitor."""
        for n in (pos, neg):
            self._register_node(n)
        self.components.append(
            Component(
                name=name,
                kind="capacitor",
                pos=pos,
                neg=neg,
                params={"value": value_f},
                comment=comment,
            ),
        )

    def add_inductor(
        self,
        name: str,
        pos: str,
        neg: str,
        value_h: float,
        *,
        comment: str | None = None,
    ) -> None:
        """Add an inductor."""
        for n in (pos, neg):
            self._register_node(n)
        self.components.append(
            Component(
                name=name,
                kind="inductor",
                pos=pos,
                neg=neg,
                params={"value": value_h},
                comment=comment,
            ),
        )

    def add_voltage_source(
        self,
        name: str,
        pos: str,
        neg: str,
        *,
        dc: float | None = None,
        ac: float | None = None,
        sin: dict | None = None,
    ) -> None:
        """Add a voltage source.

        Args:
            dc: DC voltage (for .op analysis).
            ac: AC magnitude (for .ac analysis, e.g. ac=1 means "AC 1").
            sin: sine wave params, e.g. {"amplitude": 5, "freq": 60}.
        """
        for n in (pos, neg):
            self._register_node(n)
        params: dict = {}
        if dc is not None:
            params["dc"] = dc
        if ac is not None:
            params["ac"] = ac
        if sin is not None:
            params["sin"] = dict(sin)
        self.components.append(
            Component(name=name, kind="vsource", pos=pos, neg=neg, params=params),
        )

    def add_diode(
        self,
        name: str,
        pos: str,
        neg: str,
        model: str = "1N4148",
    ) -> None:
        """Add a diode."""
        for n in (pos, neg):
            self._register_node(n)
        self.components.append(
            Component(name=name, kind="diode", pos=pos, neg=neg, params={"model": model}),
        )

    def add_directive(self, line: str) -> None:
        """Add a raw SPICE directive (e.g. .model, .ic, .options)."""
        self.directives.append(line)

    # -- serialization ----------------------------------------------------

    def to_spice(
        self,
        simulation: SimulationConfig,
        print_signals: list[str] | None = None,
    ) -> str:
        """Emit a complete Xyce netlist string from this graph.

        Delegates to ``graph.spice_emitter.emit_spice``.
        """
        from .spice_emitter import emit_spice

        return emit_spice(self, simulation, print_signals=print_signals)

    # -- validation ------------------------------------------------------

    def validate(self) -> list[str]:
        """Return a list of error messages (empty means valid)."""
        errors: list[str] = []

        # Ground must exist
        if "0" not in self.nodes:
            errors.append("ground node '0' is missing")
            return errors  # can't check connectivity without ground

        # Duplicate component names
        seen: set[str] = set()
        for c in self.components:
            if c.name in seen:
                errors.append(f"duplicate component name '{c.name}'")
            seen.add(c.name)

        # Unknown node references
        for c in self.components:
            for node in (c.pos, c.neg):
                if node not in self.nodes:
                    errors.append(f"component '{c.name}' references unknown node '{node}'")

        # At least one source
        sources = [c for c in self.components if c.kind == "vsource"]
        if not sources:
            errors.append("circuit has no voltage source")

        # Floating nodes (exactly one connection, excluding ground)
        degree: dict[str, int] = {}
        for c in self.components:
            degree[c.pos] = degree.get(c.pos, 0) + 1
            degree[c.neg] = degree.get(c.neg, 0) + 1
        for node, deg in degree.items():
            if node != "0" and deg == 1:
                errors.append(f"floating node '{node}' has only one connection")

        return errors
