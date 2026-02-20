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

        Returns a dict mapping group name to the average score (0.0–1.0).
        """
        evaluate_fn = self._evaluate_fn or (lambda gen, code: target in gen)
        evaluate_neighborhood_fn = self._evaluate_neighborhood_fn or (
            lambda gen, code: target not in gen
        )

        results = {}
        for group_name, outputs in generations_by_group.items():
            group_score = []
            for output_batch in outputs:
                for output_single in output_batch:
                    code = runnability.extract_runnable(output_single)
                    if group_name == "neighborhood":
                        group_score.append(
                            evaluate_neighborhood_fn(output_single, code)
                        )
                    else:
                        group_score.append(evaluate_fn(output_single, code))
            avg = sum(group_score) / len(group_score)
            results[group_name] = avg
        return results
