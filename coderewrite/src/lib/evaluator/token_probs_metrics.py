# File: token_probs_metrics.py
# Description: Computes efficacy, specificity, and probability-difference metrics from raw token log-probability data.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026


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


def compute_snippet_category_summaries(
    group_results: dict, in_dist_snippets: frozenset
) -> dict:
    """Compute separate efficacy summaries for in-dist and OOD snippets.

    Partitions all non-neighborhood ``(group, snippet)`` pairs using the
    explicit *in_dist_snippets* set declared in the experiment's prompts module.

    Args:
        group_results: Same shape as the input to ``compute_overall_summary``.
        in_dist_snippets: Frozenset of snippet strings that count as
                          in-distribution (from ``Prompts.in_dist_snippets``).

    Returns:
        Dict with ``"in_dist"`` and/or ``"ood"`` keys, each containing
        ``efficacy`` and ``efficacy_accuracy`` values.  A key is omitted when
        no matching pairs exist.
    """
    in_dist_sr, in_dist_ac = [], []
    ood_sr, ood_ac = [], []

    for group, snippet_dict in group_results.items():
        if group == "neighborhood":
            continue
        for snippet, data in snippet_dict.items():
            if snippet in in_dist_snippets:
                in_dist_sr.append(data["success_rate"])
                in_dist_ac.append(data["avg_correct"])
            else:
                ood_sr.append(data["success_rate"])
                ood_ac.append(data["avg_correct"])

    result = {}
    if in_dist_sr:
        result["in_dist"] = {
            "efficacy": float(np.mean(in_dist_sr)),
            "efficacy_accuracy": float(np.mean(in_dist_ac)),
        }
    if ood_sr:
        result["ood"] = {
            "efficacy": float(np.mean(ood_sr)),
            "efficacy_accuracy": float(np.mean(ood_ac)),
        }
    return result


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
