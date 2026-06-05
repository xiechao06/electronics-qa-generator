"""Tests for extraction/scoring.py — sample richness scoring."""

from __future__ import annotations

from electronics_qa_generator.extraction.scoring import (
    RichnessScore,
    compute_richness,
)
from electronics_qa_generator.simulation.models import SimResult


class TestRichnessScore:
    def test_default_values(self):
        score = RichnessScore()
        assert score.total == 0.5
        assert score.separability == 0.5
        assert score.stability == 0.5
        assert score.probe_coverage == 1.0


class TestComputeRichness:
    def test_successful_simulation_neutral(self):
        sim_result = SimResult(
            success=True,
            sim_type="op",
            raw_output="ok",
            exit_code=0,
            converged=True,
        )
        score = compute_richness({"Vout_dc": 3.0}, sim_result)
        assert score.total == 0.5
        assert score.probe_coverage == 1.0

    def test_failed_simulation_zeros(self):
        sim_result = SimResult(
            success=False,
            sim_type="op",
            raw_output="",
            exit_code=1,
            converged=False,
            error_message="fail",
        )
        score = compute_richness({}, sim_result)
        assert score.total == 0.0
        assert score.separability == 0.0
        assert score.stability == 0.0
        assert score.probe_coverage == 0.0

    def test_non_converged_zeros(self):
        sim_result = SimResult(
            success=True,
            sim_type="ac",
            raw_output="data",
            exit_code=0,
            converged=False,
        )
        score = compute_richness({}, sim_result)
        assert score.total == 0.0
