"""electronics_qa_generator.

A SPICE/Xyce-grounded pipeline for generating multimodal electronics circuit
Q/A items (MMMU-style).

Design principle (see docs/architecture.md and docs/plan.md):

    Simulation establishes facts -> code derives answers -> the LLM only
    expresses or reviews truth that has already been computed.

The package is organized as a sequence of pipeline stages:

    templates  -> sampling -> netlist -> simulation -> parsing -> extraction
    -> questions -> (llm) -> validation -> rendering -> output

Each subpackage is currently a stub to be implemented step by step.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
