"""Tests for code extraction logic in RunnabilityEvaluator."""

from src.lib.evaluator.runnability import RunnabilityEvaluator

CODE_START = "```python\n"


def make_evaluator():
    """Create a minimal evaluator for testing extraction only."""
    return RunnabilityEvaluator(code_start_tag=CODE_START)


e = make_evaluator()


# ----- _extract_fenced_blocks -----


class TestExtractFencedBlocks:
    def test_single_block(self):
        gen = "Here is code:\n```python\nprint('hi')\n```"
        assert e._extract_fenced_blocks(gen) == ["print('hi')"]

    def test_multiple_blocks(self):
        gen = "```python\nx = 1\n```\nand then\n```python\ny = 2\n```"
        assert e._extract_fenced_blocks(gen) == ["x = 1", "y = 2"]

    def test_truncated_block(self):
        gen = "```python\ndef foo():\n    return 42"
        blocks = e._extract_fenced_blocks(gen)
        assert len(blocks) == 1
        assert "def foo():" in blocks[0]

    def test_no_blocks(self):
        gen = "Just some text with no code"
        assert e._extract_fenced_blocks(gen) == []

    def test_complete_plus_truncated(self):
        gen = "```python\nx = 1\n```\nmore text\n```python\ny = 2"
        blocks = e._extract_fenced_blocks(gen)
        assert len(blocks) == 2


# ----- _deduplicate -----


class TestDeduplicate:
    def test_exact_duplicates(self):
        blocks = ["x = 1", "x = 1"]
        assert e._deduplicate(blocks) == ["x = 1"]

    def test_whitespace_duplicates(self):
        blocks = ["x  =  1", "x = 1"]
        assert len(e._deduplicate(blocks)) == 1

    def test_subset_removed(self):
        blocks = ["def foo():\n    return 1", "return 1"]
        result = e._deduplicate(blocks)
        assert len(result) == 1
        assert "def foo():" in result[0]

    def test_superset_replaces(self):
        blocks = ["return 1", "def foo():\n    return 1"]
        result = e._deduplicate(blocks)
        assert len(result) == 1
        assert "def foo():" in result[0]

    def test_distinct_blocks_kept(self):
        blocks = ["x = 1", "y = 2"]
        assert e._deduplicate(blocks) == ["x = 1", "y = 2"]


# ----- _merge_blocks -----


class TestMergeBlocks:
    def test_single_block(self):
        assert e._merge_blocks(["x = 1"]) == "x = 1"

    def test_two_valid_blocks_concatenated(self):
        blocks = ["def foo():\n    return 1", "print(foo())"]
        result = e._merge_blocks(blocks)
        assert "def foo():" in result
        assert "print(foo())" in result

    def test_all_concat_valid(self):
        blocks = ["import os", "print(os.getcwd())"]
        result = e._merge_blocks(blocks)
        assert "import os" in result
        assert "print(os.getcwd())" in result


# ----- _extract_runnable (full pipeline) -----


class TestExtractRunnable:
    def test_single_fenced_block(self):
        gen = "Here:\n```python\ndef area(w, h):\n    return w * h\n```"
        code = e._extract_runnable(gen)
        assert code is not None
        assert "def area" in code

    def test_multiple_blocks_merged(self):
        gen = (
            "Definition:\n```python\ndef area(w, h):\n    return w * h\n```\n"
            "Usage:\n```python\nprint(area(3, 4))\n```"
        )
        code = e._extract_runnable(gen)
        assert "def area" in code
        assert "print(area(3, 4))" in code

    def test_duplicate_blocks_deduped(self):
        gen = (
            "```python\ndef area(w, h):\n    return w * h\n```\n"
            "Again:\n```python\ndef area(w, h):\n    return w * h\n```"
        )
        code = e._extract_runnable(gen)
        assert code.count("def area") == 1

    def test_truncated_block_extracted(self):
        gen = "```python\ndef area(w, h):\n    return w * h"
        code = e._extract_runnable(gen)
        assert code is not None
        assert "def area" in code

    def test_bare_code_fallback(self):
        gen = "Sure, here is a function for that:\ndef area(w, h):\n    return w * h\nThis computes the area."
        code = e._extract_runnable(gen)
        assert code is not None
        assert "def area" in code

    def test_no_code_returns_none(self):
        gen = "I don't know how to do that, sorry."
        assert e._extract_runnable(gen) is None


# ----- _check_runnable -----


class TestCheckRunnable:
    def test_valid_code_returns_true_none(self):
        runnable, error = e._check_runnable("x = 1 + 1")
        assert runnable is True
        assert error is None

    def test_none_input_returns_no_code_extracted(self):
        runnable, error = e._check_runnable(None)
        assert runnable is False
        assert error == "no code extracted"

    def test_syntax_error(self):
        runnable, error = e._check_runnable("def foo(:\n    pass")
        assert runnable is False
        assert error is not None
        assert error.startswith("SyntaxError:")

    def test_zero_division_error(self):
        runnable, error = e._check_runnable("x = 1 / 0")
        assert runnable is False
        assert error is not None
        assert error.startswith("ZeroDivisionError:")

    def test_name_error(self):
        runnable, error = e._check_runnable("print(undefined_variable)")
        assert runnable is False
        assert error is not None
        assert error.startswith("NameError:")

    def test_infinite_loop_timeout(self):
        e.exec_timeout = 1  # Set a short timeout for testing
        runnable, error = e._check_runnable("while True: pass")
        assert runnable is False
        assert error is not None
        assert error.startswith("TimeoutError:")

    def test_error_format_is_type_colon_message(self):
        runnable, error = e._check_runnable("raise ValueError('bad value')")
        assert runnable is False
        assert error is not None
        exc_type, _, _ = error.partition(":")
        assert exc_type == "ValueError"


# ----- evaluate() return shape -----


class TestEvaluateReturnsErrors:
    def _make_generations(self, groups, snippet=None):
        """Build a generations_by_group dict from {group: [code_str]}.

        Each code string is wrapped in a fenced block so that
        ``extract_runnable`` can find it (mirroring real model output).
        Uses the new nested structure: {group: [{"snippet": key, "results": [...]}]}.
        """
        result = {}
        for group, codes in groups.items():
            results = [[f"```python\n{c}\n```"] for c in codes]
            result[group] = [{"snippet": snippet, "results": results}]
        return result

    def test_returns_two_tuple_of_dicts(self):
        gens = self._make_generations({"text_code": ["x = 1"]})
        ret = e.evaluate(gens)
        assert isinstance(ret, tuple)
        assert len(ret) == 2
        scores, errors = ret
        assert isinstance(scores, dict)
        assert isinstance(errors, dict)

    def test_scores_dict_has_snippet_keyed_float_values(self):
        gens = self._make_generations({"text_code": ["x = 1", "y = 2"]})
        scores, _ = e.evaluate(gens)
        # scores["text_code"] is now {snippet_key: float}
        assert isinstance(scores["text_code"], dict)
        assert isinstance(list(scores["text_code"].values())[0], float)

    def test_errors_dict_has_snippet_keyed_list_values(self):
        gens = self._make_generations({"text_code": ["x = 1", "y = 2"]})
        _, errors = e.evaluate(gens)
        assert isinstance(errors["text_code"], dict)
        assert isinstance(list(errors["text_code"].values())[0], list)

    def test_errors_list_length_matches_generations(self):
        codes = ["x = 1", "y = 2", "z = 3"]
        gens = self._make_generations({"code": codes})
        _, errors = e.evaluate(gens)
        err_list = list(errors["code"].values())[0]
        assert len(err_list) == len(codes)

    def test_successful_run_has_none_error(self):
        gens = self._make_generations({"text_code": ["x = 1"]})
        _, errors = e.evaluate(gens)
        err_list = list(errors["text_code"].values())[0]
        assert err_list[0] is None

    def test_failed_run_has_error_string(self):
        gens = self._make_generations({"text_code": ["raise RuntimeError('oops')"]})
        _, errors = e.evaluate(gens)
        err_list = list(errors["text_code"].values())[0]
        assert isinstance(err_list[0], str)
        assert "RuntimeError" in err_list[0]

    def test_neighborhood_absent_from_both_dicts(self):
        gens = self._make_generations(
            {"text_code": ["x = 1"], "neighborhood": ["y = 2"]}
        )
        scores, errors = e.evaluate(gens)
        assert "neighborhood" not in scores
        assert "neighborhood" not in errors

    def test_multiple_snippets_produce_multiple_keys(self):
        """When multiple snippets are used, each gets its own entry."""
        result = {
            "text_code": [
                {"snippet": "snippet_a", "results": [["```python\nx = 1\n```"]]},
                {"snippet": "snippet_b", "results": [["```python\ny = 2\n```"]]},
            ]
        }
        scores, errors = e.evaluate(result)
        assert set(scores["text_code"].keys()) == {"snippet_a", "snippet_b"}
        assert set(errors["text_code"].keys()) == {"snippet_a", "snippet_b"}
