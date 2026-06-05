"""Xyce invocation with timeout, retry, and convergence detection.

Core simulation stage: takes a netlist string, runs Xyce, returns SimResult.
"""

from __future__ import annotations

import random
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..graph.models import CircuitGraph
from ..models import SimulationConfig
from .models import SimResult

# ---------------------------------------------------------------------------
# Xyce availability check
# ---------------------------------------------------------------------------


def check_xyce_installed() -> None:
    """Raise RuntimeError if Xyce is not on PATH."""
    if shutil.which("xyce") is None:
        raise RuntimeError("Xyce not found on PATH. Install from https://xyce.sandia.gov/")


# ---------------------------------------------------------------------------
# Low-level invocation
# ---------------------------------------------------------------------------


def invoke_xyce(netlist: str, timeout_s: int = 30) -> tuple[str, int, bool]:
    """Run Xyce on a netlist string and return (stdout, returncode, converged).

    The netlist is written to a temporary .cir file that Xyce reads.
    """
    check_xyce_installed()

    with tempfile.NamedTemporaryFile(suffix=".cir", mode="w", delete=False) as f:
        cir_path = Path(f.name)
        f.write(netlist)

    try:
        result = subprocess.run(
            ["xyce", str(cir_path), "-quiet"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        stdout = result.stdout
        returncode = result.returncode
        # Xyce convergence: look for "Solution by Newton" or similar marker
        converged = "Solution by Newton" in stdout and returncode == 0
    except subprocess.TimeoutExpired:
        stdout = ""
        returncode = -1
        converged = False
    finally:
        # Clean up temp file and any Xyce-generated files
        cir_path.unlink(missing_ok=True)
        for ext in (".prn", ".out", ".log", ".res", ".mt0", ".txt"):
            for generated in cir_path.parent.glob(f"{cir_path.stem}{ext}"):
                generated.unlink(missing_ok=True)

    return stdout, returncode, converged


# ---------------------------------------------------------------------------
# Retry with perturbation
# ---------------------------------------------------------------------------


def _perturb_resistors(
    graph: CircuitGraph,
    rng: random.Random | None = None,
    delta: float = 0.05,
) -> CircuitGraph:
    """Create a new CircuitGraph with resistor values perturbed by ±delta.

    Only resistors are perturbed; other component types are copied as-is.
    """
    if rng is None:
        rng = random.Random()

    new_graph = CircuitGraph(header_comment=graph.header_comment)

    for comp in graph.components:
        if comp.kind == "resistor":
            factor = 1.0 + rng.uniform(-delta, delta)
            new_value = comp.params["value"] * factor
            new_graph.add_resistor(
                comp.name,
                comp.pos,
                comp.neg,
                new_value,
                comment=comp.comment,
            )
        elif comp.kind == "capacitor":
            new_graph.add_capacitor(
                comp.name,
                comp.pos,
                comp.neg,
                comp.params["value"],
                comment=comp.comment,
            )
        elif comp.kind == "inductor":
            new_graph.add_inductor(
                comp.name,
                comp.pos,
                comp.neg,
                comp.params["value"],
                comment=comp.comment,
            )
        elif comp.kind == "vsource":
            new_graph.add_voltage_source(
                comp.name,
                comp.pos,
                comp.neg,
                **comp.params,
            )
        elif comp.kind == "diode":
            new_graph.add_diode(
                comp.name,
                comp.pos,
                comp.neg,
                model=comp.params.get("model", "1N4148"),
            )

    for directive in graph.directives:
        new_graph.add_directive(directive)

    return new_graph


def run_xyce_with_retry(
    graph: CircuitGraph,
    simulation: SimulationConfig,
    max_attempts: int = 3,
    timeout_s: int = 30,
) -> SimResult:
    """Run Xyce with retry-on-failure and resistor perturbation.

    On convergence failure, resistor values are perturbed by ±5% and
    the simulation is retried, up to *max_attempts* total runs.
    """
    rng = random.Random()
    last_error: str | None = None

    current_graph = graph

    for attempt in range(max_attempts):
        # Pause re-generates because we mutated the graph
        if attempt > 0:
            current_graph = _perturb_resistors(graph, rng)

        netlist = current_graph.to_spice(
            simulation,
            print_signals=None,  # use defaults
        )

        try:
            stdout, returncode, converged = invoke_xyce(netlist, timeout_s)
        except RuntimeError as e:
            return SimResult(
                success=False,
                sim_type=simulation.type,
                raw_output="",
                exit_code=-1,
                error_message=str(e),
                converged=False,
            )

        if converged:
            return SimResult(
                success=True,
                sim_type=simulation.type,
                raw_output=stdout,
                exit_code=returncode,
                converged=True,
            )

        last_error = f"attempt {attempt + 1}: convergence failed"
        # Also capture any stderr if available
        if returncode != 0 and stdout:
            last_error += f" (rc={returncode})"

    return SimResult(
        success=False,
        sim_type=simulation.type,
        raw_output="",
        exit_code=-1,
        error_message=last_error or "all retry attempts failed",
        converged=False,
    )
