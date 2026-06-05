"""Handler for the `eqa emit` subcommand.

Drives template sampling, writes netlist + JSON record to stdout or files.
Optionally renders a schematic PNG with ``--render``.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from ..models import CircuitRecord
from ..templates import ALL_TEMPLATES, CircuitTemplate
from .serialize import record_to_json

logger = logging.getLogger(__name__)


# -- template lookup -----------------------------------------------------------

_TEMPLATE_BY_TOPOLOGY: dict[str, CircuitTemplate] = {t.topology: t for t in ALL_TEMPLATES}
_VALID_NAMES = sorted(_TEMPLATE_BY_TOPOLOGY.keys())


def get_template(name: str) -> CircuitTemplate:
    """Return the template instance for *name*.

    Raises SystemExit with a helpful message when the name is unknown.
    """
    try:
        return _TEMPLATE_BY_TOPOLOGY[name]
    except KeyError:
        names = ", ".join(_VALID_NAMES)
        print(f"error: unknown topology '{name}'. Valid: {names}", file=sys.stderr)
        raise SystemExit(2)


# -- emit helpers --------------------------------------------------------------


def _seed_str(seed: int) -> str:
    return f"{seed & 0xFFFFFFFF:08x}"


def _emit_one(
    template: CircuitTemplate,
    seed: int,
    *,
    out_dir: Path | None,
    render: bool = False,
) -> None:
    """Sample *template* and output netlist + JSON record.

    When *render* is True, also produces a schematic PNG.
    """
    record: CircuitRecord = template.sample(seed=seed)
    netlist = record.netlist
    json_str = record_to_json(record)

    # Determine output path for the schematic
    base = f"{record.topology}_{_seed_str(seed)}"
    schematic_path: str | None = None
    if render and record.graph is not None:
        try:
            from ..render.schematic import render_schematic
        except ImportError:
            logger.warning(
                "matplotlib not installed — cannot render schematic. "
                "Install with: uv sync --extra render"
            )
        else:
            render_dir = (out_dir / "images" / record.topology) if out_dir else Path("out/images") / record.topology
            render_dir.mkdir(parents=True, exist_ok=True)
            seed_str = _seed_str(seed)
            png_path = render_dir / f"{seed_str}.png"
            render_schematic(record.graph, png_path)
            schematic_path = f"images/{record.topology}/{seed_str}.png"

    if out_dir is None:
        # stdout mode
        print(netlist)
        print("# --- record.json ---")
        print(json_str)
        if schematic_path:
            print(f"# schematic: {schematic_path}")
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        cir_path = out_dir / f"{base}.cir"
        json_path = out_dir / f"{base}.json"
        cir_path.write_text(netlist + "\n")
        json_path.write_text(json_str + "\n")
        if schematic_path:
            print(f"schematic: {out_dir / schematic_path}")


def _emit_all(seed: int, *, out_dir: Path | None, render: bool = False) -> None:
    """Emit every template in ALL_TEMPLATES."""
    for template in ALL_TEMPLATES:
        _emit_one(template, seed=seed, out_dir=out_dir, render=render)


# -- main entry point ----------------------------------------------------------


def run_emit(args) -> None:
    """Execute `eqa emit` logic from parsed CLI args."""
    seed: int = args.seed

    if args.list:
        for name in _VALID_NAMES:
            print(name)
        return

    out_dir: Path | None = None
    render: bool = getattr(args, "render", False)
    if args.out:
        out_dir = Path(args.out).resolve()

    if args.all:
        _emit_all(seed, out_dir=out_dir, render=render)
        return

    # Single-template mode — topology is required unless --list or --all
    if args.topology is None:
        print("error: specify a topology or use --list / --all", file=sys.stderr)
        raise SystemExit(2)

    template = get_template(args.topology)
    _emit_one(template, seed=seed, out_dir=out_dir, render=render)
