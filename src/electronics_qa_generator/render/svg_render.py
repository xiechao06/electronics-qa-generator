"""SVG-based schematic renderer.

Fills hand-authored SVG layout templates with sampled circuit values,
reference designators, and node labels, then rasterizes to PNG.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ..graph.models import CircuitGraph
from .format import format_component_label
from .svg_templates import SVGTemplate

__all__ = ["render_svg_schematic", "fill_template"]

logger = logging.getLogger(__name__)

# Rasterization constants
_DEFAULT_DPI = 100
_DEFAULT_SCALE = 1.0  # pixels per user unit at 96 dpi; cairosvg handles scaling


def render_svg_schematic(
    graph: CircuitGraph,
    template: SVGTemplate,
    output_path: Path,
    *,
    dpi: float = _DEFAULT_DPI,
) -> None:
    """Fill an SVG template with graph data and rasterize to PNG.

    Parameters
    ----------
    graph : CircuitGraph
        The circuit to render.
    template : SVGTemplate
        Resolved and validated SVG layout template.
    output_path : Path
        Output PNG file path (parent dirs created if needed).
    dpi : float
        DPI for rasterization (default 100).
    """
    import cairosvg  # noqa: F401 — lazy import to keep base install working

    output_path.parent.mkdir(parents=True, exist_ok=True)

    filled_svg = fill_template(graph, template)

    cairosvg.svg2png(
        bytestring=filled_svg.encode("utf-8"),
        write_to=str(output_path),
        dpi=dpi,
        output_width=800,
        output_height=400,
        background_color="white",
    )


# -- Slot filling ------------------------------------------------------------


# Regex to find text elements with slot ids and extract their text content
_SLOT_TEXT_RE = re.compile(
    r'(<text[^>]*\bid="(slot-[\w.\-]+)"[^>]*>)(.*?)(</text>)',
    re.DOTALL,
)


def fill_template(graph: CircuitGraph, template: SVGTemplate) -> str:
    """Fill a template's value and node slots with the graph's actual data.

    Value slots are filled using ``format_component_label`` so labels
    match the rest of the pipeline.  Node slots receive the bare node name.

    Parameters
    ----------
    graph : CircuitGraph
        Sampled circuit whose values/labels/nodes are substituted.
    template : SVGTemplate
        SVG layout template with named slots.

    Returns
    -------
    str
        Complete SVG string with all slots filled.
    """
    svg = template.svg_content

    # Build lookup maps
    # Component ref → label
    ref_to_label: dict[str, str] = {}
    for comp in graph.components:
        ref_to_label[comp.name] = format_component_label(comp.name, comp.kind, comp.params)

    # Node name lookup
    node_to_label: dict[str, str] = {node: node for node in graph.non_ground_nodes}

    def _replacer(match: re.Match) -> str:
        prefix = match.group(1)  # <text ...id="slot-X"...>
        slot_id = match.group(2)  # slot-R1, slot-node-in, etc.
        suffix = match.group(4)  # </text>

        new_text = ""
        if slot_id.startswith("slot-node-"):
            node_name = slot_id.removeprefix("slot-node-")
            new_text = node_to_label.get(node_name, slot_id)
        elif slot_id.startswith("slot-param-"):
            param_name = slot_id.removeprefix("slot-param-")
            param_val = graph.params.get(param_name)
            if param_val is not None:
                new_text = str(param_val)
            else:
                new_text = slot_id
        else:
            ref = slot_id.removeprefix("slot-")
            new_text = ref_to_label.get(ref, slot_id)

        return f"{prefix}{new_text}{suffix}"

    return _SLOT_TEXT_RE.sub(_replacer, svg)
