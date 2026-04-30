"""Custom evaluation logic for target-match scoring."""

from typing import Callable

from .runnability import RunnabilityEvaluator, RunnabilityExtractionType


def _call_evaluate(fn, generation, code):
    """Call fn; normalize bool or (bool, reason) to (passed, reason).

    When the evaluator returns ``None`` (or ``(None, reason)``), the sample
    is indeterminate and ``(None, reason)`` is returned as a skip signal.
    Callers must filter ``None`` scores before aggregating.
    """
    result = fn(generation, code)
    if isinstance(result, tuple):
        passed, reason = result
        if passed is None:
            return None, reason
        passed = bool(passed)
        return passed, (None if passed else reason)
    if result is None:
        return None, None
    passed = bool(result)
    return passed, None


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
            extract_mode = (
                RunnabilityExtractionType.MERGE
                if group_name == "long_tasks"
                else RunnabilityExtractionType.SECOND
                if group_name == "reversion"
                else None
            )
            for entry in snippet_entries:
                key = entry["snippet"]
                group_score = []
                for output_batch in entry["results"]:
                    for output_single in output_batch:
                        code = runnability.extract_runnable(
                            output_single, mode=extract_mode
                        )
                        if group_name == "neighborhood":
                            passed, _ = _call_evaluate(
                                evaluate_neighborhood_fn, output_single, code
                            )
                        else:
                            passed, _ = _call_evaluate(evaluate_fn, output_single, code)
                        if passed is not None:
                            group_score.append(passed)
                snippet_results[key] = (
                    sum(group_score) / len(group_score) if group_score else None
                )
            results[group_name] = snippet_results
        return results

    def evaluate_raw(
        self,
        target: str,
        generations_by_group: dict,
        runnability: RunnabilityEvaluator,
    ) -> tuple[dict, dict]:
        """Like evaluate(), but returns per-generation score lists instead of averages.

        Returns a tuple ``(scores_dict, reasons_dict)`` where:
          - ``scores_dict``: ``{group: {snippet_key: [bool, ...]}}``
          - ``reasons_dict``: ``{group: {snippet_key: [str | None, ...]}}``
        """
        evaluate_fn = self._evaluate_fn or (lambda gen, code: target in gen)
        evaluate_neighborhood_fn = self._evaluate_neighborhood_fn or (
            lambda gen, code: target not in gen
        )

        scores = {}
        reasons = {}
        for group_name, snippet_entries in generations_by_group.items():
            snippet_scores = {}
            snippet_reasons = {}
            extract_mode = (
                RunnabilityExtractionType.MERGE
                if group_name == "long_tasks"
                else RunnabilityExtractionType.SECOND
                if group_name == "reversion"
                else None
            )
            for entry in snippet_entries:
                key = entry["snippet"]
                group_scores = []
                group_reasons = []
                for output_batch in entry["results"]:
                    for output_single in output_batch:
                        code = runnability.extract_runnable(
                            output_single, mode=extract_mode
                        )
                        if group_name == "neighborhood":
                            passed, reason = _call_evaluate(
                                evaluate_neighborhood_fn, output_single, code
                            )
                        else:
                            passed, reason = _call_evaluate(
                                evaluate_fn, output_single, code
                            )
                        group_scores.append(passed)
                        group_reasons.append(reason)
                snippet_scores[key] = group_scores
                snippet_reasons[key] = group_reasons
            scores[group_name] = snippet_scores
            reasons[group_name] = snippet_reasons
        return scores, reasons
