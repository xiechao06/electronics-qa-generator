"""Schematic PNG renderer from CircuitGraph.

Renders a complete circuit schematic image using matplotlib, with automatic
left-to-right layout for single-loop series circuits (the 5 MVP topologies).
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..graph.models import CircuitGraph
from .format import format_component_label
from .symbols import (
    FONT_SIZE_LABEL,
    FONT_SIZE_NODE,
    LINE_WIDTH,
    SYMBOL_LENGTH,
    draw_capacitor,
    draw_diode,
    draw_ground,
    draw_inductor,
    draw_resistor,
    draw_voltage_source,
)

logger = logging.getLogger(__name__)

# -- Layout constants (in data coords matching 100 dpi) ----------------------

_FIG_WIDTH = 800
_FIG_HEIGHT = 400
_DPI = 100

_TOP_Y = 100.0  # top rail y-coordinate
_BOTTOM_Y = 300.0  # bottom rail / ground y-coordinate
_LEFT_X = 100.0  # start of the layout area
_RIGHT_X = 700.0  # end of the layout area

_COMP_SPACING = SYMBOL_LENGTH + 40.0  # horizontal gap between component centers
_LABEL_OFFSET_Y = -30.0  # label below the component


# -- Symbol dispatcher -------------------------------------------------------

_SYMBOL_DRAWERS = {
    "resistor": draw_resistor,
    "capacitor": draw_capacitor,
    "inductor": draw_inductor,
    "diode": draw_diode,
    "vsource": draw_voltage_source,
}


# -- Main render function ----------------------------------------------------


def render_schematic(
    graph: CircuitGraph,
    output_path: Path,
    *,
    width: int = _FIG_WIDTH,
    height: int = _FIG_HEIGHT,
    dpi: int = _DPI,
) -> None:
    """Render a ``CircuitGraph`` as a schematic PNG.

    This produces a single-loop left-to-right schematic layout suitable for
    all 5 MVP topologies (voltage divider, RC low-pass, RC high-pass,
    RLC band-pass, half-wave rectifier).

    Parameters
    ----------
    graph : CircuitGraph
        The circuit to render.
    output_path : Path
        Output PNG file path (parent dirs created if needed).
    width : int
        Image width in pixels at the given dpi.
    height : int
        Image height in pixels.
    dpi : int
        DPI for deterministic rendering.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.axis("off")

    # Separate components: source vs. passive
    sources = graph.components_by_kind("vsource")
    passives = [c for c in graph.components if c.kind != "vsource"]

    # ---- Layout: source on the left (vertical), passives horizontally ----
    center_x = _LEFT_X
    mid_point = (_TOP_Y + _BOTTOM_Y) / 2

    # Source: vertical orientation
    src_x = center_x
    src = sources[0] if sources else None
    if src is not None:
        # Draw source vertically centered
        draw_voltage_source(ax, src_x, mid_point, angle=90)
        # Source label
        src_label = format_component_label(src.name, src.kind, src.params)
        ax.text(
            src_x,
            mid_point + _LABEL_OFFSET_Y,
            src_label,
            ha="center",
            va="top",
            fontsize=FONT_SIZE_LABEL,
        )
        center_x += _COMP_SPACING

    # Passive components: horizontal left-to-right
    n = len(passives)
    for i, comp in enumerate(passives):
        comp_x = center_x
        is_last = i == n - 1

        if not is_last:
            # Horizontal placement on top rail
            draw_symbol = _SYMBOL_DRAWERS.get(comp.kind)
            if draw_symbol:
                draw_symbol(ax, comp_x, _TOP_Y, angle=0)
            # Label
            label = format_component_label(comp.name, comp.kind, comp.params)
            ax.text(
                comp_x + SYMBOL_LENGTH / 2,
                _TOP_Y + _LABEL_OFFSET_Y,
                label,
                ha="center",
                va="top",
                fontsize=FONT_SIZE_LABEL,
            )
            center_x += _COMP_SPACING
        else:
            # Last component: drop vertically to bottom rail
            # Draw horizontal segment then vertical down
            # Top horizontal lead
            ax.plot(
                [comp_x - _COMP_SPACING * 0.3, comp_x],
                [_TOP_Y, _TOP_Y],
                "k-",
                lw=LINE_WIDTH,
            )
            draw_symbol = _SYMBOL_DRAWERS.get(comp.kind)
            if draw_symbol:
                draw_symbol(ax, comp_x, (_TOP_Y + _BOTTOM_Y) / 2, angle=90)
            # Vertical lead down to bottom rail
            # (symbol draws its own leads, but connect to bottom)
            ax.plot(
                [comp_x, comp_x],
                [(_TOP_Y + _BOTTOM_Y) / 2 + SYMBOL_LENGTH / 2 + 10, _BOTTOM_Y],
                "k-",
                lw=LINE_WIDTH,
            )
            # Label to the right of vertical symbol
            label = format_component_label(comp.name, comp.kind, comp.params)
            ax.text(
                comp_x + _LABEL_OFFSET_Y,
                (_TOP_Y + _BOTTOM_Y) / 2,
                label,
                ha="left",
                va="center",
                fontsize=FONT_SIZE_LABEL,
            )
            center_x += _COMP_SPACING * 0.5

    # ---- Connecting wires ----
    # Top rail: from source top to first component
    if sources:
        src_top_y = mid_point + 30
        ax.plot(
            [_LEFT_X, _LEFT_X], [_BOTTOM_Y, src_top_y], "k-", lw=LINE_WIDTH
        )  # source vertical wire
    if passives:
        # Top rail from source area to last horizontal component
        wire_start_x = _LEFT_X + _COMP_SPACING - SYMBOL_LENGTH / 2
        if n > 1:
            wire_end_x = center_x - _COMP_SPACING - _COMP_SPACING * 0.3
        else:
            wire_end_x = _LEFT_X + _COMP_SPACING - 20
        ax.plot([wire_start_x, wire_end_x], [_TOP_Y, _TOP_Y], "k-", lw=LINE_WIDTH)

    # Bottom rail from end back to source
    ax.plot(
        [wire_start_x, _LEFT_X],
        [_BOTTOM_Y, _BOTTOM_Y],
        "k-",
        lw=LINE_WIDTH,
    )

    # ---- Ground at source bottom ----
    draw_ground(ax, _LEFT_X, _BOTTOM_Y)

    # ---- Node labels ----
    node_positions: dict[str, tuple[float, float]] = {
        "in": (_LEFT_X + 30, _TOP_Y),
        "out": (_LEFT_X + _COMP_SPACING + SYMBOL_LENGTH / 2, _TOP_Y),
        "0": (_LEFT_X, _BOTTOM_Y - 20),
    }
    for node_name, (nx, ny) in node_positions.items():
        if node_name != "0" or True:  # always show "0" as GND label
            label_text = node_name if node_name != "0" else ""
            if label_text:
                ax.text(nx, ny, label_text, ha="center", va="bottom", fontsize=FONT_SIZE_NODE)

    # ---- Save ----
    fig.savefig(str(output_path), dpi=dpi, facecolor="white", edgecolor="none")
    plt.close(fig)
