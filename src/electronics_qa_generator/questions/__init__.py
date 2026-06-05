"""Question template engine + deterministic answer generator.

Generates candidate questions from the fact table (direct numeric, derived
numeric, multiple-choice, classification, comparison, trend, counterfactual,
fault diagnosis, multimodal) and computes exact answers, units, tolerances,
and correct MC option indices. CLEVR-inspired: every question has a
machine-readable program (see docs/circuit_qa_program_language.md). Answers
never depend on the LLM.
"""
