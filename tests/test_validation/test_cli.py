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


class TestVerifyTemplatesCli:
    def test_verify_templates_passes_and_exits_zero(self, capsys):
        """eqa verify-templates exits 0 when all topologies pass."""
        from electronics_qa_generator.cli import main

        rc = main(["verify-templates"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "topologies pass" in out

    def test_verify_templates_json(self, capsys):
        """--json emits machine-readable output."""
        import json

        from electronics_qa_generator.cli import main

        rc = main(["verify-templates", "--json"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["passed"] is True
        assert payload["topologies"]

    def test_verify_templates_failure_exits_nonzero(self, monkeypatch, capsys):
        """A coverage failure causes a non-zero exit and prints the locus."""
        import pytest

        from electronics_qa_generator.cli import main
        from electronics_qa_generator.validation import cli_handler
        from electronics_qa_generator.validation.template_coverage import (
            CoverageFailure,
            CoverageReport,
            TopologyReport,
        )

        bad = CoverageReport(
            topologies=[
                TopologyReport(
                    family="opamp",
                    topology="op_amp_inverting",
                    failures=[
                        CoverageFailure(
                            kind="hidden_input",
                            locus="opamp_inv_bw:Cpole",
                            detail="value of 'Cpole' is needed but not shown",
                        )
                    ],
                )
            ]
        )
        monkeypatch.setattr(cli_handler, "verify_all", lambda **_: bad, raising=False)
        # Patch the imported symbol used inside run_verify_templates.
        import electronics_qa_generator.validation.template_coverage as tc

        monkeypatch.setattr(tc, "verify_all", lambda **_: bad)

        with pytest.raises(SystemExit) as exc:
            main(["verify-templates"])
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "Cpole" in out
