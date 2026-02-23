"""Tests for custom evaluation logic in CustomEvaluator."""

from src.lib.evaluator.custom import CustomEvaluator
from src.lib.evaluator.runnability import RunnabilityEvaluator

CODE_START = "```python\n"


def _make_gens(groups_dict, snippet=None):
    """Wrap a {group: [gen_str, ...]} dict into the nested snippet structure."""
    return {
        group: [{"snippet": snippet, "results": [[g] for g in gens]}]
        for group, gens in groups_dict.items()
    }


def _score(scores, group, snippet=None):
    """Extract the averaged score for a (group, snippet) pair."""
    return scores[group][snippet]


class TestCustomEvaluators:
    @staticmethod
    def _evaluate(target, generations_dict, **kwargs):
        """Helper: run CustomEvaluator.evaluate() with the given generations."""
        runnability = RunnabilityEvaluator(code_start_tag=CODE_START)
        custom = CustomEvaluator(**kwargs)
        return custom.evaluate(target, generations_dict, runnability)

    def test_default_substring_match(self):
        """Default evaluate_fn uses substring match on target."""
        scores = self._evaluate(
            target="width ** height",
            generations_dict=_make_gens({"text_code": ["return width ** height"]}),
        )
        assert _score(scores, "text_code") == 1.0

    def test_default_substring_miss(self):
        scores = self._evaluate(
            target="width ** height",
            generations_dict=_make_gens({"text_code": ["return width * height"]}),
        )
        assert _score(scores, "text_code") == 0.0

    def test_default_neighborhood_inverted(self):
        """Default neighborhood check: target NOT in generation = pass."""
        scores = self._evaluate(
            target="width ** height",
            generations_dict=_make_gens({"neighborhood": ["return width * height"]}),
        )
        assert _score(scores, "neighborhood") == 1.0

    def test_default_neighborhood_fail(self):
        scores = self._evaluate(
            target="width ** height",
            generations_dict=_make_gens({"neighborhood": ["return width ** height"]}),
        )
        assert _score(scores, "neighborhood") == 0.0

    def test_custom_evaluate_fn_called(self):
        """Custom evaluate_fn receives generation and extracted code."""
        calls = []

        def custom_eval(generation, code):
            calls.append((generation, code))
            return "CUSTOM_MATCH" in generation

        scores = self._evaluate(
            target="ignored",
            generations_dict=_make_gens({"text_code": ["has CUSTOM_MATCH here"]}),
            evaluate_fn=custom_eval,
        )
        assert _score(scores, "text_code") == 1.0
        assert len(calls) == 1
        assert calls[0][0] == "has CUSTOM_MATCH here"

    def test_custom_evaluate_fn_miss(self):
        def custom_eval(generation, code):
            return "CUSTOM_MATCH" in generation

        scores = self._evaluate(
            target="ignored",
            generations_dict=_make_gens({"text_code": ["no match"]}),
            evaluate_fn=custom_eval,
        )
        assert _score(scores, "text_code") == 0.0

    def test_custom_neighborhood_fn_called(self):
        calls = []

        def custom_neighborhood(generation, code):
            calls.append((generation, code))
            return "BAD_PATTERN" not in generation

        scores = self._evaluate(
            target="ignored",
            generations_dict=_make_gens({"neighborhood": ["clean output"]}),
            evaluate_neighborhood_fn=custom_neighborhood,
        )
        assert _score(scores, "neighborhood") == 1.0
        assert len(calls) == 1

    def test_custom_neighborhood_fn_fail(self):
        def custom_neighborhood(generation, code):
            return "BAD_PATTERN" not in generation

        scores = self._evaluate(
            target="ignored",
            generations_dict=_make_gens({"neighborhood": ["has BAD_PATTERN here"]}),
            evaluate_neighborhood_fn=custom_neighborhood,
        )
        assert _score(scores, "neighborhood") == 0.0

    def test_custom_fn_receives_extracted_code(self):
        """Verify that the code parameter is the extracted runnable code."""
        codes_seen = []

        def custom_eval(generation, code):
            codes_seen.append(code)
            return True

        self._evaluate(
            target="ignored",
            generations_dict=_make_gens({"text_code": ["```python\nx = 42\n```"]}),
            evaluate_fn=custom_eval,
        )
        assert codes_seen[0] is not None
        assert "x = 42" in codes_seen[0]

    def test_custom_fn_receives_none_when_no_code(self):
        """Code param is None when no runnable code can be extracted."""
        codes_seen = []

        def custom_eval(generation, code):
            codes_seen.append(code)
            return True

        self._evaluate(
            target="ignored",
            generations_dict=_make_gens({"text_code": ["just plain text, no code"]}),
            evaluate_fn=custom_eval,
        )
        assert codes_seen[0] is None
