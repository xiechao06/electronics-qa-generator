"""Verifier, quality filters, and split checks.

Verifier: question matches stored facts, answer matches computed value, no unit
mismatch, no ambiguity, no answer leakage, plots visibly support the question.
Quality filters reject failed/unstable/trivial/duplicate/unreadable samples.
Split checks guard against leakage across train/val/test (docs/plan.md 7).
"""
