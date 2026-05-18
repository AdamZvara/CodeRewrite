# File: test_token_probs_metrics.py
# Description: Unit tests for token_probs_metrics computing efficacy, specificity, and summary statistics.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026


import math

import pytest

from src.lib.evaluator.token_probs_metrics import (
    compute_group_metrics,
    compute_overall_summary,
)


class TestComputeGroupMetrics:
    def test_regular_all_success(self):
        """target_new NLL < target_true NLL → success_rate=1.0 for non-neighborhood."""
        probs = [
            {"target_new": 0.5, "target_true": 1.0},
            {"target_new": 0.3, "target_true": 0.8},
        ]
        correct = [True, True]
        result = compute_group_metrics(probs, correct, is_neighborhood=False)
        assert result["success_rate"] == 1.0
        assert result["prob_diff"] > 0

    def test_neighborhood_all_success(self):
        """target_true NLL < target_new NLL → success_rate=1.0 for neighborhood."""
        probs = [
            {"target_new": 1.0, "target_true": 0.5},
            {"target_new": 0.8, "target_true": 0.3},
        ]
        correct = [True, True]
        result = compute_group_metrics(probs, correct, is_neighborhood=True)
        assert result["success_rate"] == 1.0
        assert result["prob_diff"] > 0

    def test_mixed_regular(self):
        """Half succeed, half fail → success_rate=0.5."""
        probs = [
            {"target_new": 0.5, "target_true": 1.0},  # success: new < true
            {"target_new": 1.0, "target_true": 0.5},  # failure: new > true
        ]
        correct = [True, False]
        result = compute_group_metrics(probs, correct, is_neighborhood=False)
        assert result["success_rate"] == pytest.approx(0.5)

    def test_prob_diff_value_regular(self):
        """Verify prob_diff calculation: mean(exp(-new) - exp(-true))."""
        probs = [{"target_new": 1.0, "target_true": 2.0}]
        correct = [True]
        result = compute_group_metrics(probs, correct, is_neighborhood=False)
        expected_diff = math.exp(-1.0) - math.exp(-2.0)
        assert result["prob_diff"] == pytest.approx(expected_diff, abs=1e-6)

    def test_prob_diff_value_neighborhood(self):
        """Verify prob_diff calculation for neighborhood: mean(exp(-true) - exp(-new))."""
        probs = [{"target_new": 2.0, "target_true": 1.0}]
        correct = [True]
        result = compute_group_metrics(probs, correct, is_neighborhood=True)
        expected_diff = math.exp(-1.0) - math.exp(-2.0)
        assert result["prob_diff"] == pytest.approx(expected_diff, abs=1e-6)

    def test_empty_probs(self):
        """Empty input returns zero values without error."""
        result = compute_group_metrics([], [], is_neighborhood=False)
        assert result["success_rate"] == 0.0
        assert result["prob_diff"] == 0.0


class TestComputeOverallSummary:
    def _make_group(self, success_rate, avg_correct, snippet=None):
        """Wrap metrics in the snippet-keyed structure expected by compute_overall_summary."""
        return {
            snippet: {
                "probs": [],
                "correct": [],
                "avg_correct": avg_correct,
                "success_rate": success_rate,
                "prob_diff": 0.0,
            }
        }

    def test_with_neighborhood(self):
        """Score is harmonic mean of efficacy and specificity."""
        group_results = {
            "text_code": self._make_group(0.8, 0.7),
            "neighborhood": self._make_group(0.6, 0.5),
        }
        summary = compute_overall_summary(group_results)

        assert summary["efficacy"] == pytest.approx(0.8)
        assert summary["efficacy_accuracy"] == pytest.approx(0.7)
        assert summary["specificity"] == pytest.approx(0.6)
        assert summary["specificity_accuracy"] == pytest.approx(0.5)

        expected_score = 2 * 0.8 * 0.6 / (0.8 + 0.6)
        assert summary["score"] == pytest.approx(expected_score, abs=1e-6)

    def test_no_neighborhood(self):
        """When neighborhood is absent, score key is not present."""
        group_results = {
            "text_code": self._make_group(0.75, 0.6),
            "code": self._make_group(0.65, 0.55),
        }
        summary = compute_overall_summary(group_results)

        assert summary["efficacy"] == pytest.approx(0.70)
        assert summary["efficacy_accuracy"] == pytest.approx(0.575)
        assert "specificity" not in summary
        assert "score" not in summary

    def test_multiple_non_neighborhood_groups_averaged(self):
        """Efficacy is the mean over all non-neighborhood groups."""
        group_results = {
            "text_code": self._make_group(1.0, 1.0),
            "code": self._make_group(0.0, 0.0),
        }
        summary = compute_overall_summary(group_results)
        assert summary["efficacy"] == pytest.approx(0.5)
        assert summary["efficacy_accuracy"] == pytest.approx(0.5)
