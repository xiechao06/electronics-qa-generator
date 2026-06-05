"""Tests for the `eqa emit` subcommand.

Covers stdout mode, file mode, --list, --all, error handling, and reproducibility.
"""

from __future__ import annotations

import json
import subprocess
import sys


def _eqa(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "electronics_qa_generator.cli", *args],
        capture_output=True,
        text=True,
    )


# -- --list --------------------------------------------------------------------


class TestList:
    def test_lists_all_five(self):
        result = _eqa("emit", "--list")
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert set(lines) == {
            "voltage_divider",
            "rc_lowpass",
            "rc_highpass",
            "rlc_bandpass",
            "half_wave_rectifier",
        }


# -- single emit stdout --------------------------------------------------------


class TestSingleEmitStdout:
    def test_prints_netlist_and_json(self):
        result = _eqa("emit", "rc_lowpass", "--seed", "42")
        assert result.returncode == 0
        assert "* RC low-pass filter" in result.stdout
        assert ".end" in result.stdout
        assert "# --- record.json ---" in result.stdout
        assert '"topology": "rc_lowpass"' in result.stdout

    def test_json_is_parseable(self):
        result = _eqa("emit", "rc_lowpass", "--seed", "1")
        _, _, json_str = result.stdout.partition("# --- record.json ---\n")
        parsed = json.loads(json_str)
        assert parsed["topology"] == "rc_lowpass"
        assert parsed["family"] == "passive"

    def test_seed_changes_output(self):
        a = _eqa("emit", "voltage_divider", "--seed", "10")
        b = _eqa("emit", "voltage_divider", "--seed", "20")
        assert a.stdout != b.stdout


# -- unknown topology error ----------------------------------------------------


class TestUnknownTopology:
    def test_error_and_nonzero_exit(self):
        result = _eqa("emit", "nosuch")
        assert result.returncode != 0
        assert "unknown topology" in result.stderr
        assert "nosuch" in result.stderr

    def test_error_lists_valid_names(self):
        result = _eqa("emit", "bad")
        assert "voltage_divider" in result.stderr
        assert "rc_lowpass" in result.stderr
        assert "half_wave_rectifier" in result.stderr


# -- file mode -----------------------------------------------------------------


class TestSingleFileMode:
    def test_writes_cir_and_json(self, tmp_path):
        out = tmp_path / "build"
        result = _eqa("emit", "rc_highpass", "--seed", "5", "-o", str(out))
        assert result.returncode == 0
        cirs = list(out.glob("rc_highpass_*.cir"))
        jsons = list(out.glob("rc_highpass_*.json"))
        assert len(cirs) == 1
        assert len(jsons) == 1
        assert cirs[0].read_text().startswith("*")
        assert ".end" in cirs[0].read_text()
        data = json.loads(jsons[0].read_text())
        assert data["topology"] == "rc_highpass"

    def test_creates_output_dir(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        assert not nested.exists()
        result = _eqa("emit", "rc_lowpass", "--seed", "3", "-o", str(nested))
        assert result.returncode == 0
        assert nested.exists()
        assert len(list(nested.glob("*.cir"))) == 1

    def test_file_naming_includes_seed(self, tmp_path):
        out = tmp_path / "emitted"
        _eqa("emit", "voltage_divider", "--seed", "42", "-o", str(out))
        # seed=42 → 0000002a
        cirs = list(out.glob("*.cir"))
        assert len(cirs) == 1
        assert "0000002a" in cirs[0].name


class TestAllFileMode:
    def test_writes_pair_per_template(self, tmp_path):
        out = tmp_path / "all"
        result = _eqa("emit", "--all", "--seed", "7", "-o", str(out))
        assert result.returncode == 0

        cir_files = sorted(out.glob("*.cir"))
        json_files = sorted(out.glob("*.json"))
        assert len(cir_files) == 5
        assert len(json_files) == 5


# -- reproducibility -----------------------------------------------------------


class TestReproducibility:
    def test_same_seed_byte_identical_files(self, tmp_path):
        a_dir = tmp_path / "a"
        b_dir = tmp_path / "b"
        _eqa("emit", "rc_lowpass", "--seed", "42", "-o", str(a_dir))
        _eqa("emit", "rc_lowpass", "--seed", "42", "-o", str(b_dir))

        a_cirs = sorted(a_dir.glob("*.cir"))
        b_cirs = sorted(b_dir.glob("*.cir"))
        assert len(a_cirs) == 1
        assert a_cirs[0].read_bytes() == b_cirs[0].read_bytes()

        a_jsons = sorted(a_dir.glob("*.json"))
        b_jsons = sorted(b_dir.glob("*.json"))
        assert a_jsons[0].read_bytes() == b_jsons[0].read_bytes()

    def test_same_seed_byte_identical_stdout(self):
        a = subprocess.run(
            [
                sys.executable,
                "-m",
                "electronics_qa_generator.cli",
                "emit",
                "rc_lowpass",
                "--seed",
                "99",
            ],
            capture_output=True,
        )
        b = subprocess.run(
            [
                sys.executable,
                "-m",
                "electronics_qa_generator.cli",
                "emit",
                "rc_lowpass",
                "--seed",
                "99",
            ],
            capture_output=True,
        )
        assert a.stdout == b.stdout


# -- edge cases ----------------------------------------------------------------


class TestEdgeCases:
    def test_no_args_shows_error(self):
        result = _eqa("emit")
        assert result.returncode != 0
