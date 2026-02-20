"""Human-interpretable metrics derived from raw token-probability outputs."""

import numpy as np


def compute_group_metrics(
    probs: list,
    correct: list,
    is_neighborhood: bool,
) -> dict:
    """Return success_rate and prob_diff for a single prompt group.

    For non-neighborhood: success when target_new NLL < target_true NLL
      (edit was adopted — edited target is more likely than original).
    For neighborhood: success when target_true NLL < target_new NLL
      (edit did not leak — original target is still more likely).

    Args:
        probs: List of dicts {"target_new": float, "target_true": float}
               (average negative log-prob, lower = more likely).
        correct: List of booleans from compute_token_probabilities.
        is_neighborhood: Whether this group is the neighborhood group.

    Returns:
        Dict with keys success_rate and prob_diff.
    """
    if not probs:
        return {"success_rate": 0.0, "prob_diff": 0.0}

    if is_neighborhood:
        success_rate = float(
            np.mean([x["target_true"] < x["target_new"] for x in probs])
        )
        prob_diff = float(
            np.mean(
                [np.exp(-x["target_true"]) - np.exp(-x["target_new"]) for x in probs]
            )
        )
    else:
        success_rate = float(
            np.mean([x["target_true"] > x["target_new"] for x in probs])
        )
        prob_diff = float(
            np.mean(
                [np.exp(-x["target_new"]) - np.exp(-x["target_true"]) for x in probs]
            )
        )

    return {"success_rate": success_rate, "prob_diff": prob_diff}


def compute_overall_summary(group_results: dict) -> dict:
    """Aggregate group metrics into top-level efficacy / specificity / score.

    - efficacy: mean success_rate across all non-neighborhood groups
    - efficacy_accuracy: mean avg_correct across non-neighborhood groups
    - specificity: neighborhood success_rate (if present)
    - specificity_accuracy: neighborhood avg_correct (if present)
    - score: harmonic mean of [efficacy, specificity] when both are available

    Args:
        group_results: Dict mapping group names to group result dicts,
                       each containing success_rate and avg_correct keys.

    Returns:
        Summary dict with the keys described above.
    """
    non_neighborhood = {k: v for k, v in group_results.items() if k != "neighborhood"}
    neighborhood = group_results.get("neighborhood")

    summary = {}

    if non_neighborhood:
        summary["efficacy"] = float(
            np.mean([v["success_rate"] for v in non_neighborhood.values()])
        )
        summary["efficacy_accuracy"] = float(
            np.mean([v["avg_correct"] for v in non_neighborhood.values()])
        )

    if neighborhood is not None:
        summary["specificity"] = float(neighborhood["success_rate"])
        summary["specificity_accuracy"] = float(neighborhood["avg_correct"])

    if "efficacy" in summary and "specificity" in summary:
        e = summary["efficacy"]
        s = summary["specificity"]
        denom = e + s
        summary["score"] = float(2 * e * s / denom) if denom > 0 else 0.0

    return summary
