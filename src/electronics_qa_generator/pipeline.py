"""End-to-end pipeline orchestration (skeleton).

Implements the core flow from docs/plan.md section 5. Each stage is a stub for
now; fill them in step by step.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .models import Sample


def generate_dataset(n: int = 1000) -> Iterator[Sample]:
    """Generate accepted dataset samples.

    The intended flow (not yet implemented):

        for template in templates:
            circuit  = template.sample()
            netlist  = write_netlist(circuit)
            result   = run_xyce(netlist)
            if not result.success:
                continue
            facts    = extract_facts(result)
            if not passes_quality_filters(circuit, facts):
                continue
            qa_pairs = generate_questions(circuit, facts)
            yield assemble_sample(circuit, result, facts, qa_pairs)
    """
    raise NotImplementedError("pipeline stages not implemented yet")


def assemble(samples: Iterable[Sample]) -> list[Sample]:
    """Collect samples into a list (placeholder for the dataset assembler)."""
    return list(samples)
