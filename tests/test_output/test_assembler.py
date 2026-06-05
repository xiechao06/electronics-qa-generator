"""Tests for output/assembler.py — MMMU JSONL dataset assembly."""

from __future__ import annotations

import json

from electronics_qa_generator.models import QAItem
from electronics_qa_generator.output.assembler import assemble_dataset


def _make_item(**kwargs) -> QAItem:
    defaults = {
        "question_type": "direct",
        "question": "Find the cutoff frequency.",
        "answer": "233 Hz",
        "answer_value": 233.0,
        "unit": "Hz",
        "tolerance": 0.5,
        "program": [],
    }
    defaults.update(kwargs)
    return QAItem(**defaults)


class TestAssembleDataset:
    def test_direct_question_format(self, tmp_path):
        item = _make_item()
        out = assemble_dataset([item], [None], "rc_lowpass", 42, tmp_path)

        lines = out.read_text().strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])

        assert record["id"] == "rc_lowpass_0000002a_0"
        assert record["question"] == "Find the cutoff frequency."
        assert record["answer"] == "233 Hz"
        assert "options" not in record
        assert "explanation" not in record  # None, omitted

    def test_id_format(self, tmp_path):
        item = _make_item()
        out = assemble_dataset([item], [None], "voltage_divider", 255, tmp_path)
        record = json.loads(out.read_text().strip())
        assert record["id"] == "voltage_divider_000000ff_0"

    def test_classification_with_options(self, tmp_path):
        item = _make_item(
            question_type="classification",
            question="Classify the filter.",
            answer="low-pass",
            choices=["low-pass", "high-pass", "band-pass"],
        )
        out = assemble_dataset([item], [None], "rc_lowpass", 42, tmp_path)
        record = json.loads(out.read_text().strip())
        assert "options" in record
        assert record["answer"] == "low-pass"

    def test_explanation_included(self, tmp_path):
        item = _make_item(explanation="The cutoff is given by 1/(2πRC).")
        out = assemble_dataset([item], [None], "rc_lowpass", 42, tmp_path)
        record = json.loads(out.read_text().strip())
        assert record["explanation"] == "The cutoff is given by 1/(2πRC)."

    def test_schematic_copied(self, tmp_path):
        # Create a fake PNG
        png = tmp_path / "fake.png"
        png.write_bytes(b"\x89PNG\x00\x00")

        item = _make_item()
        out = assemble_dataset([item], [str(png)], "rc_lowpass", 42, tmp_path)
        record = json.loads(out.read_text().strip())
        assert "image" in record
        assert record["image"] == "images/rc_lowpass/0000002a.png"
        assert (tmp_path / "images" / "rc_lowpass" / "0000002a.png").exists()

    def test_missing_schematic_omitted(self, tmp_path):
        item = _make_item()
        out = assemble_dataset([item], [None], "rc_lowpass", 42, tmp_path)
        record = json.loads(out.read_text().strip())
        assert "image" not in record


class TestAssembleCLI:
    def test_assemble_help(self):
        import sys
        from io import StringIO

        from electronics_qa_generator.cli import build_parser

        parser = build_parser()
        old = sys.stdout
        try:
            sys.stdout = StringIO()
            try:
                parser.parse_args(["assemble", "--help"])
            except SystemExit:
                pass
            text = sys.stdout.getvalue()
        finally:
            sys.stdout = old
        assert "assemble" in text.lower()
        assert "--out" in text
