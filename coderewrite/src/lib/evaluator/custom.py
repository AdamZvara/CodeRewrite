"""Custom evaluation logic for target-match scoring."""

from typing import Callable

from .runnability import RunnabilityEvaluator


class CustomEvaluator:
    """Applies per-experiment scoring functions to generations.

    For regular groups, the default scoring function checks that ``target``
    appears in the generation (edit success). For the ``neighborhood`` group,
    the default checks that ``target`` does NOT appear, verifying that the
    edit did not bleed into unrelated knowledge.
    """

    def __init__(
        self,
        evaluate_fn: Callable = None,
        evaluate_neighborhood_fn: Callable = None,
    ):
        self._evaluate_fn = evaluate_fn
        self._evaluate_neighborhood_fn = evaluate_neighborhood_fn

    def evaluate(
        self,
        target: str,
        generations_by_group: dict,
        runnability: RunnabilityEvaluator,
    ) -> dict:
        """Score each prompt group on target match.

        Accepts the nested snippet structure produced by
        ``Generator.generate()``::

            {group: [{"snippet": str | None, "results": [[gen, ...], ...]}, ...]}

        Returns ``{group: {snippet_key: avg_score}}``.
        """
        evaluate_fn = self._evaluate_fn or (lambda gen, code: target in gen)
        evaluate_neighborhood_fn = self._evaluate_neighborhood_fn or (
            lambda gen, code: target not in gen
        )

        results = {}
        for group_name, snippet_entries in generations_by_group.items():
            snippet_results = {}
            for entry in snippet_entries:
                key = entry["snippet"]
                group_score = []
                for output_batch in entry["results"]:
                    for output_single in output_batch:
                        code = runnability.extract_runnable(output_single)
                        if group_name == "neighborhood":
                            group_score.append(
                                evaluate_neighborhood_fn(output_single, code)
                            )
                        else:
                            group_score.append(evaluate_fn(output_single, code))
                snippet_results[key] = sum(group_score) / len(group_score)
            results[group_name] = snippet_results
        return results
