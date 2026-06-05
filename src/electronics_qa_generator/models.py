"""Core data models shared across pipeline stages.

These dataclasses define the structured record that flows through the pipeline,
mirroring the sample record described in docs/plan.md (section 4) and
docs/architecture.md. They are intentionally minimal stubs to be expanded as
each stage is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimulationConfig:
    """How a circuit should be simulated (.op/.dc/.ac/.tran)."""

    type: str
    tool: str = "Xyce"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitRecord:
    """A sampled circuit: the bridge between generation, simulation, and Q/A."""

    id: str
    family: str
    topology: str
    difficulty: int
    parameters: dict[str, Any] = field(default_factory=dict)
    netlist: str = ""
    simulation: SimulationConfig | None = None
    probes: list[str] = field(default_factory=list)
    graph: Any = None  # CircuitGraph (lazy-typed to avoid circular import)


@dataclass
class QAItem:
    """A single question/answer item grounded in the fact table.

    `program` is the CLEVR-style machine-readable form
    (see docs/circuit_qa_program_language.md).
    """

    question_type: str
    question: str
    answer: str
    answer_value: float | None = None
    unit: str | None = None
    tolerance: float | None = None
    choices: list[str] | None = None
    program: list[dict[str, Any]] | None = None
    explanation: str | None = None


@dataclass
class Sample:
    """A fully assembled dataset record."""

    circuit: CircuitRecord
    facts: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    qa: list[QAItem] = field(default_factory=list)
