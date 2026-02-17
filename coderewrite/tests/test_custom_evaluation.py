"""Tests for custom evaluation logic in BaselineEvaluator."""

from src.lib.evaluate import BaselineEvaluator

CODE_START = "```python\n"


class TestCustomEvaluators:
    @staticmethod
    def _make_evaluator_with_generations(target, generations_dict, **kwargs):
        ev = BaselineEvaluator(
            generate_fn=None,
            model=None,
            target=target,
            code_start_tag=CODE_START,
            **kwargs,
        )
        ev.generations = generations_dict
        return ev

    def test_default_substring_match(self):
        """Default evaluate_fn uses substring match on target."""
        ev = self._make_evaluator_with_generations(
            target="width ** height",
            generations_dict={
                "text_code": [["return width ** height"]],
            },
        )
        scores = ev.evaluate_score()
        assert scores["text_code"] == 1.0

    def test_default_substring_miss(self):
        ev = self._make_evaluator_with_generations(
            target="width ** height",
            generations_dict={
                "text_code": [["return width * height"]],
            },
        )
        scores = ev.evaluate_score()
        assert scores["text_code"] == 0.0

    def test_default_neighborhood_inverted(self):
        """Default neighborhood check: target NOT in generation = pass."""
        ev = self._make_evaluator_with_generations(
            target="width ** height",
            generations_dict={
                "neighborhood": [["return width * height"]],
            },
        )
        scores = ev.evaluate_score()
        assert scores["neighborhood"] == 1.0

    def test_default_neighborhood_fail(self):
        ev = self._make_evaluator_with_generations(
            target="width ** height",
            generations_dict={
                "neighborhood": [["return width ** height"]],
            },
        )
        scores = ev.evaluate_score()
        assert scores["neighborhood"] == 0.0

    def test_custom_evaluate_fn_called(self):
        """Custom evaluate_fn receives generation and extracted code."""
        calls = []

        def custom_eval(generation, code):
            calls.append((generation, code))
            return "CUSTOM_MATCH" in generation

        ev = self._make_evaluator_with_generations(
            target="ignored",
            generations_dict={
                "text_code": [["has CUSTOM_MATCH here"]],
            },
            evaluate_fn=custom_eval,
        )
        scores = ev.evaluate_score()
        assert scores["text_code"] == 1.0
        assert len(calls) == 1
        assert calls[0][0] == "has CUSTOM_MATCH here"

    def test_custom_evaluate_fn_miss(self):
        def custom_eval(generation, code):
            return "CUSTOM_MATCH" in generation

        ev = self._make_evaluator_with_generations(
            target="ignored",
            generations_dict={
                "text_code": [["no match"]],
            },
            evaluate_fn=custom_eval,
        )
        scores = ev.evaluate_score()
        assert scores["text_code"] == 0.0

    def test_custom_neighborhood_fn_called(self):
        calls = []

        def custom_neighborhood(generation, code):
            calls.append((generation, code))
            return "BAD_PATTERN" not in generation

        ev = self._make_evaluator_with_generations(
            target="ignored",
            generations_dict={
                "neighborhood": [["clean output"]],
            },
            evaluate_neighborhood_fn=custom_neighborhood,
        )
        scores = ev.evaluate_score()
        assert scores["neighborhood"] == 1.0
        assert len(calls) == 1

    def test_custom_neighborhood_fn_fail(self):
        def custom_neighborhood(generation, code):
            return "BAD_PATTERN" not in generation

        ev = self._make_evaluator_with_generations(
            target="ignored",
            generations_dict={
                "neighborhood": [["has BAD_PATTERN here"]],
            },
            evaluate_neighborhood_fn=custom_neighborhood,
        )
        scores = ev.evaluate_score()
        assert scores["neighborhood"] == 0.0

    def test_custom_fn_receives_extracted_code(self):
        """Verify that the code parameter is the extracted runnable code."""
        codes_seen = []

        def custom_eval(generation, code):
            codes_seen.append(code)
            return True

        ev = self._make_evaluator_with_generations(
            target="ignored",
            generations_dict={
                "text_code": [["```python\nx = 42\n```"]],
            },
            evaluate_fn=custom_eval,
        )
        ev.evaluate_score()
        assert codes_seen[0] is not None
        assert "x = 42" in codes_seen[0]

    def test_custom_fn_receives_none_when_no_code(self):
        """Code param is None when no runnable code can be extracted."""
        codes_seen = []

        def custom_eval(generation, code):
            codes_seen.append(code)
            return True

        ev = self._make_evaluator_with_generations(
            target="ignored",
            generations_dict={
                "text_code": [["just plain text, no code"]],
            },
            evaluate_fn=custom_eval,
        )
        ev.evaluate_score()
        assert codes_seen[0] is None
