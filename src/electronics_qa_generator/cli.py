"""Command-line interface for the electronics Q/A generator.

Exposed as the `eqa` console script (see pyproject.toml). This is a minimal
skeleton; subcommands will be wired to pipeline stages as they are implemented.
"""

from __future__ import annotations

import argparse

from . import __version__


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        print(f"[eqa] generate requested: n={args.num}, out={args.out!r}")
        print("[eqa] pipeline not implemented yet — see docs/plan.md")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
