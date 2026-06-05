"""Schematic PNG renderer from CircuitGraph.

Renders a complete circuit schematic image. When an SVG layout template
is registered for the circuit's topology, the hand-authored SVG is filled
and rasterized; otherwise the existing matplotlib auto-layout is used.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..graph.models import CircuitGraph
from .format import format_component_label
from .symbols import (
    FONT_SIZE_LABEL,
    FONT_SIZE_NODE,
    LEAD_LENGTH,
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

    If an SVG layout template is registered for the graph's topology,
    the template is filled with the sampled circuit's values and
    rasterized via cairosvg. Otherwise, the matplotlib auto-layout
    is used for single-loop series circuits.

    Parameters
    ----------
    graph : CircuitGraph
        The circuit to render.
    output_path : Path
        Output PNG file path (parent dirs created if needed).
    width : int
        Image width in pixels at the given dpi (matplotlib path only).
    height : int
        Image height in pixels (matplotlib path only).
    dpi : int
        DPI for deterministic rendering.
    """
    # -- SVG template path (when a hand-authored layout is available) -----
    try:
        from .svg_templates import registry

        if registry.has_template(graph):
            tpl = registry.resolve(graph)
            from .svg_render import render_svg_schematic as _svg_render

            _svg_render(graph, tpl, output_path, dpi=dpi)
            return
    except ImportError:
        logger.debug("cairosvg not installed; falling back to matplotlib")

    # -- Fallback: matplotlib auto-layout ---------------------------------
    _render_matplotlib(graph, output_path, width=width, height=height, dpi=dpi)


# -- Matplotlib fallback renderer -------------------------------------------


def _render_matplotlib(
    graph: CircuitGraph,
    output_path: Path,
    *,
    width: int = _FIG_WIDTH,
    height: int = _FIG_HEIGHT,
    dpi: int = _DPI,
) -> None:
    """Render a CircuitGraph as a schematic PNG using matplotlib auto-layout."""
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
    src = sources[0] if sources else None
    if src is not None:
        draw_voltage_source(ax, _LEFT_X, mid_point, angle=90)
        src_label = format_component_label(src.name, src.kind, src.params)
        ax.text(
            _LEFT_X,
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
            draw_symbol = _SYMBOL_DRAWERS.get(comp.kind)
            if draw_symbol:
                draw_symbol(ax, comp_x, _TOP_Y, angle=0)
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
            ax.plot(
                [comp_x - _COMP_SPACING * 0.3, comp_x],
                [_TOP_Y, _TOP_Y],
                "k-",
                lw=LINE_WIDTH,
            )
            # Vertical wire from top rail down to symbol top
            ax.plot(
                [comp_x, comp_x],
                [_TOP_Y, (_TOP_Y + _BOTTOM_Y) / 2 - SYMBOL_LENGTH / 2],
                "k-",
                lw=LINE_WIDTH,
            )
            draw_symbol = _SYMBOL_DRAWERS.get(comp.kind)
            if draw_symbol:
                draw_symbol(ax, comp_x, (_TOP_Y + _BOTTOM_Y) / 2, angle=90)
            # Vertical wire from symbol bottom to bottom rail
            ax.plot(
                [comp_x, comp_x],
                [(_TOP_Y + _BOTTOM_Y) / 2 + SYMBOL_LENGTH / 2, _BOTTOM_Y],
                "k-",
                lw=LINE_WIDTH,
            )
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
    if sources:
        # Wire from source top lead to top rail
        src_top_lead_y = mid_point - LEAD_LENGTH
        ax.plot([_LEFT_X, _LEFT_X], [src_top_lead_y, _TOP_Y], "k-", lw=LINE_WIDTH)
        # Wire from source bottom to bottom rail
        src_bottom_lead_y = mid_point + LEAD_LENGTH
        ax.plot([_LEFT_X, _LEFT_X], [src_bottom_lead_y, _BOTTOM_Y], "k-", lw=LINE_WIDTH)
        # Horizontal wire from source x to first component area on top rail
        wire_start_x = _LEFT_X + _COMP_SPACING - SYMBOL_LENGTH / 2
        ax.plot([_LEFT_X, wire_start_x], [_TOP_Y, _TOP_Y], "k-", lw=LINE_WIDTH)
    if passives:
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
        if node_name != "0" or True:
            label_text = node_name if node_name != "0" else ""
            if label_text:
                ax.text(
                    nx,
                    ny,
                    label_text,
                    ha="center",
                    va="bottom",
                    fontsize=FONT_SIZE_NODE,
                )

    # ---- Save ----
    fig.savefig(str(output_path), dpi=dpi, facecolor="white", edgecolor="none")
    plt.close(fig)
