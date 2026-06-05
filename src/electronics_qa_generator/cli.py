"""Command-line interface for the electronics Q/A generator.

Exposed as the `eqa` console script (see pyproject.toml). This is a minimal
skeleton; subcommands will be wired to pipeline stages as they are implemented.
"""

from __future__ import annotations

import argparse

from . import __version__
from .output.emit import run_emit
from .questions.cli_handler import run_questions
from .simulation.cli_handler import run_simulate
from .validation.cli_handler import run_validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eqa",
        description="Generate MMMU-style multimodal electronics circuit Q/A items.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate", help="generate a dataset (not yet implemented)")
    gen.add_argument("-n", "--num", type=int, default=1000, help="number of samples")
    gen.add_argument("-o", "--out", default="dataset", help="output directory")

    # -- emit subcommand ---------------------------------------------------
    emit = sub.add_parser("emit", help="sample templates and emit netlist + JSON record")
    emit.add_argument(
        "topology",
        nargs="?",
        default=None,
        help="topology name to emit (use --list to see available)",
    )
    emit.add_argument("--list", action="store_true", help="list available template topologies")
    emit.add_argument("--all", action="store_true", help="emit all templates")
    emit.add_argument("--seed", type=int, default=0, help="random seed for reproducible sampling")
    emit.add_argument("-o", "--out", default=None, help="output directory (default: stdout)")
    emit.add_argument(
        "--render",
        action="store_true",
        help="render a schematic PNG alongside the netlist/JSON",
    )

    # -- simulate subcommand ------------------------------------------------
    sim = sub.add_parser("simulate", help="run Xyce simulation and extract facts")
    sim.add_argument(
        "topology",
        nargs="?",
        default=None,
        help="topology name to simulate (use --list to see available)",
    )
    sim.add_argument("--list", action="store_true", help="list available template topologies")
    sim.add_argument("--all", action="store_true", help="simulate all templates")
    sim.add_argument("--seed", type=int, default=0, help="random seed for reproducible sampling")
    sim.add_argument("--cache-dir", default=None, help="fact cache directory")
    sim.add_argument("--no-cache", action="store_true", help="skip cache read/write")

    # -- questions subcommand -----------------------------------------------
    qa = sub.add_parser("questions", help="generate QA items from simulation facts")
    qa.add_argument(
        "topology",
        nargs="?",
        default=None,
        help="topology name (use --list to see available)",
    )
    qa.add_argument("--list", action="store_true", help="list topologies with question counts")
    qa.add_argument("--seed", type=int, default=0, help="random seed for reproducible sampling")
    qa.add_argument("--cache-dir", default=None, help="fact cache directory")
    qa.add_argument("--no-cache", action="store_true", help="skip cache read/write")
    qa.add_argument("--jsonl", action="store_true", help="output one JSON object per line")
    qa.add_argument(
        "--humanize",
        action="store_true",
        help="rewrite questions in natural exam-style language via DeepSeek LLM",
    )
    qa.add_argument("-o", "--out", default=None, help="output directory for rendered schematics")
    qa.add_argument(
        "--render",
        action="store_true",
        help="render a schematic PNG for each circuit alongside QA items",
    )
    qa.add_argument(
        "--verify",
        action="store_true",
        help="run static validation checks on generated QA items",
    )
    qa.add_argument(
        "--llm",
        action="store_true",
        help="run LLM-assisted checks (requires --verify)",
    )

    # -- validate subcommand ------------------------------------------------
    val = sub.add_parser("validate", help="run static QA-item checks and print report")
    val.add_argument(
        "topology",
        nargs="?",
        default=None,
        help="topology name to validate (use --list to see available)",
    )
    val.add_argument("--list", action="store_true", help="list available topologies")
    val.add_argument("--seed", type=int, default=0, help="random seed for reproducible sampling")
    val.add_argument("--cache-dir", default=None, help="fact cache directory")
    val.add_argument("--no-cache", action="store_true", help="skip cache read/write")
    val.add_argument("--json", action="store_true", help="output report as JSON")
    val.add_argument(
        "--llm",
        action="store_true",
        help="run LLM-assisted checks (ambiguity, leakage, difficulty)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        print(f"[eqa] generate requested: n={args.num}, out={args.out!r}")
        print("[eqa] pipeline not implemented yet — see docs/plan.md")
        return 0

    if args.command == "emit":
        run_emit(args)
        return 0

    if args.command == "simulate":
        run_simulate(args)
        return 0

    if args.command == "questions":
        run_questions(args)
        return 0

    if args.command == "validate":
        run_validate(args)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
