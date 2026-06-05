"""Tests for eqa validate CLI and --verify flag."""

from __future__ import annotations

import sys
from io import StringIO


class TestValidateCli:
    def test_validate_list(self):
        """eqa validate --list shows available topologies."""
        from electronics_qa_generator.cli import main

        rc = main(["validate", "--list"])
        assert rc == 0

    def test_validate_flag_in_help(self):
        """validate subcommand appears in help."""
        from electronics_qa_generator.cli import build_parser

        parser = build_parser()
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            try:
                parser.parse_args(["validate", "--help"])
            except SystemExit:
                pass
            help_text = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert "validate" in help_text.lower() or "topology" in help_text.lower()

    def test_verify_flag_in_questions_help(self):
        """--verify appears in eqa questions --help."""
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
        assert "--verify" in help_text
