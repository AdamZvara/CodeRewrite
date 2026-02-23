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

    - efficacy: mean success_rate across all non-neighborhood groups and snippets
    - efficacy_accuracy: mean avg_correct across non-neighborhood groups and snippets
    - specificity: neighborhood success_rate averaged across snippets (if present)
    - specificity_accuracy: neighborhood avg_correct averaged across snippets
    - score: harmonic mean of [efficacy, specificity] when both are available

    Args:
        group_results: Dict mapping group names to snippet-keyed dicts, each
                       of which maps a snippet key to a result dict containing
                       ``success_rate`` and ``avg_correct`` keys.

    Returns:
        Summary dict with the keys described above.
    """
    non_neighborhood = {k: v for k, v in group_results.items() if k != "neighborhood"}
    neighborhood = group_results.get("neighborhood")

    summary = {}

    if non_neighborhood:
        all_success_rates = []
        all_avg_corrects = []
        for snippet_dict in non_neighborhood.values():
            for snippet_data in snippet_dict.values():
                all_success_rates.append(snippet_data["success_rate"])
                all_avg_corrects.append(snippet_data["avg_correct"])
        summary["efficacy"] = float(np.mean(all_success_rates))
        summary["efficacy_accuracy"] = float(np.mean(all_avg_corrects))

    if neighborhood is not None:
        neigh_success = [v["success_rate"] for v in neighborhood.values()]
        neigh_correct = [v["avg_correct"] for v in neighborhood.values()]
        summary["specificity"] = float(np.mean(neigh_success))
        summary["specificity_accuracy"] = float(np.mean(neigh_correct))

    if "efficacy" in summary and "specificity" in summary:
        e = summary["efficacy"]
        s = summary["specificity"]
        denom = e + s
        summary["score"] = float(2 * e * s / denom) if denom > 0 else 0.0

    return summary
