"""Tests for simulation/runner.py — Xyce invocation and retry.

Unit tests mock the subprocess call since Xyce may not be installed.
"""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from electronics_qa_generator.graph.models import CircuitGraph
from electronics_qa_generator.models import SimulationConfig
from electronics_qa_generator.simulation.models import SimResult
from electronics_qa_generator.simulation.runner import (
    check_xyce_installed,
    invoke_xyce,
    run_xyce_with_retry,
    _perturb_resistors,
)


# ---------------------------------------------------------------------------
# SimResult
# ---------------------------------------------------------------------------


class TestSimResult:
    def test_fields_exist(self):
        sr = SimResult(
            success=True,
            sim_type="op",
            raw_output="data",
            exit_code=0,
        )
        assert sr.success
        assert sr.sim_type == "op"
        assert sr.raw_output == "data"
        assert sr.exit_code == 0
        assert sr.converged is False  # default

    def test_error_message_default(self):
        sr = SimResult(success=True, sim_type="op", raw_output="", exit_code=0)
        assert sr.error_message is None


# ---------------------------------------------------------------------------
# check_xyce_installed
# ---------------------------------------------------------------------------


class TestCheckXyce:
    def test_raises_when_not_installed(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="Xyce not found"):
                check_xyce_installed()

    def test_passes_when_installed(self):
        with patch("shutil.which", return_value="/usr/bin/xyce"):
            check_xyce_installed()  # should not raise


# ---------------------------------------------------------------------------
# invoke_xyce (mocked)
# ---------------------------------------------------------------------------

CONVERGED_OUTPUT = """\
* Xyce simulation

Solution by Newton: 3 iterations

Index   V(out)
------  ------
     0  3.14159
"""

FAILED_OUTPUT = """\
* Xyce simulation

Convergence failure in DC analysis.
"""


class TestInvokeXyce:
    @pytest.fixture(autouse=True)
    def _mock_subprocess(self):
        with (
            patch("shutil.which", return_value="/usr/bin/xyce"),
            patch("pathlib.Path.unlink"),
            patch("pathlib.Path.glob", return_value=[]),
        ):
            yield

    def test_converged_run(self):
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = type(
                "Result", (), {"stdout": CONVERGED_OUTPUT, "returncode": 0}
            )()
            stdout, rc, converged = invoke_xyce("* test\n.end")
            assert rc == 0
            assert converged
            assert "3.14159" in stdout

    def test_failed_run(self):
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = type("Result", (), {"stdout": FAILED_OUTPUT, "returncode": 1})()
            stdout, rc, converged = invoke_xyce("* test\n.end")
            assert not converged
            assert rc == 1

    def test_timeout(self):
        with patch.object(subprocess, "run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("xyce", 30)
            stdout, rc, converged = invoke_xyce("* test\n.end", timeout_s=1)
            assert rc == -1
            assert not converged


# ---------------------------------------------------------------------------
# _perturb_resistors
# ---------------------------------------------------------------------------


class TestPerturbResistors:
    def test_resistor_values_changed(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "out", 1000.0)
        g.add_resistor("R2", "out", "0", 2000.0)

        import random

        rng = random.Random(42)
        g2 = _perturb_resistors(g, rng)

        r1_new = g2.components_by_kind("resistor")[0].params["value"]
        r2_new = g2.components_by_kind("resistor")[1].params["value"]
        # Values should be within ±5% of originals
        assert 950 <= r1_new <= 1050
        assert 1900 <= r2_new <= 2100

    def test_non_resistor_components_preserved(self):
        g = CircuitGraph()
        g.add_voltage_source("Vin", "in", "0", ac=1)
        g.add_capacitor("C1", "out", "0", 1e-7)
        g.add_diode("D1", "in", "out")

        import random

        g2 = _perturb_resistors(g, random.Random(1))
        caps = g2.components_by_kind("capacitor")
        assert len(caps) == 1
        assert caps[0].params["value"] == 1e-7

    def test_directives_preserved(self):
        g = CircuitGraph()
        g.add_directive(".model D1N4148 D (Is=2.52n)")
        import random

        g2 = _perturb_resistors(g, random.Random(1))
        assert g2.directives == [".model D1N4148 D (Is=2.52n)"]


# ---------------------------------------------------------------------------
# run_xyce_with_retry (mocked)
# ---------------------------------------------------------------------------


class TestRunXyceWithRetry:
    def test_success_first_attempt(self):
        g = CircuitGraph(header_comment="* test")
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "0", 1000)

        with (
            patch("shutil.which", return_value="/usr/bin/xyce"),
            patch("electronics_qa_generator.simulation.runner.invoke_xyce") as mock_invoke,
        ):
            mock_invoke.return_value = (CONVERGED_OUTPUT, 0, True)
            result = run_xyce_with_retry(
                g,
                SimulationConfig(type="op"),
                max_attempts=3,
            )
            assert result.success
            assert result.converged
            assert mock_invoke.call_count == 1

    def test_retry_on_failure(self):
        g = CircuitGraph(header_comment="* test")
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "0", 1000)

        with (
            patch("shutil.which", return_value="/usr/bin/xyce"),
            patch("electronics_qa_generator.simulation.runner.invoke_xyce") as mock_invoke,
        ):
            # Fail twice, succeed on third
            mock_invoke.side_effect = [
                (FAILED_OUTPUT, 1, False),
                (FAILED_OUTPUT, 1, False),
                (CONVERGED_OUTPUT, 0, True),
            ]
            result = run_xyce_with_retry(
                g,
                SimulationConfig(type="op"),
                max_attempts=3,
            )
            assert result.success
            assert mock_invoke.call_count == 3

    def test_all_attempts_fail(self):
        g = CircuitGraph(header_comment="* test")
        g.add_voltage_source("Vin", "in", "0", dc=5)
        g.add_resistor("R1", "in", "0", 1000)

        with (
            patch("shutil.which", return_value="/usr/bin/xyce"),
            patch("electronics_qa_generator.simulation.runner.invoke_xyce") as mock_invoke,
        ):
            mock_invoke.return_value = (FAILED_OUTPUT, 1, False)
            result = run_xyce_with_retry(
                g,
                SimulationConfig(type="op"),
                max_attempts=3,
            )
            assert not result.success
            assert mock_invoke.call_count == 3
