"""Tests for CLI --render flag integration."""

from __future__ import annotations

import sys
from io import StringIO


class TestEmitRender:
    def test_render_flag_produces_schematic(self, tmp_path):
        """`eqa emit voltage_divider --render` produces a PNG file."""
        from electronics_qa_generator.cli import main

        out_dir = tmp_path / "output"
        # Build argv for single topology + render + out
        rc = main(["emit", "voltage_divider", "--seed", "42", "--out", str(out_dir), "--render"])
        # Should exit 0
        assert rc == 0
        # Check that a schematic PNG was created (now in per-topology subdirectory)
        png_files = list((out_dir / "images").rglob("*.png"))
        assert len(png_files) >= 1

    def test_render_without_flag_does_not_produce_png(self, tmp_path):
        """Without --render, no PNG is produced."""
        from electronics_qa_generator.cli import main

        out_dir = tmp_path / "output"
        rc = main(["emit", "voltage_divider", "--seed", "42", "--out", str(out_dir)])
        assert rc == 0
        render_dir = out_dir / "render"
        assert not render_dir.exists()


class TestQuestionsRender:
    def test_render_flag_in_help(self):
        """--render appears in eqa questions --help."""
        from electronics_qa_generator.cli import build_parser

        parser = build_parser()
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            try:
                parser.parse_args(["questions", "--help"])
            except SystemExit:
                pass
            help_text = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert "--render" in help_text

    def test_emit_render_flag_in_help(self):
        """--render appears in eqa emit --help."""
        from electronics_qa_generator.cli import build_parser

        parser = build_parser()
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            try:
                parser.parse_args(["emit", "--help"])
            except SystemExit:
                pass
            help_text = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert "--render" in help_text
