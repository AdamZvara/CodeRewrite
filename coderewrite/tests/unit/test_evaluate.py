"""Tests for code extraction logic in RunnabilityEvaluator."""

from src.lib.evaluator.runnability import (
    RunnabilityEvaluator,
    RunnabilityExtractionType,
)

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

    def test_multiple_blocks_first_mode_returns_first_only(self):
        gen = (
            "Definition:\n```python\ndef area(w, h):\n    return w * h\n```\n"
            "Usage:\n```python\nprint(area(3, 4))\n```"
        )
        code = e._extract_runnable(gen)  # default is "first"
        assert "def area" in code
        assert "print(area(3, 4))" not in code

    def test_multiple_blocks_merge_mode_combines_all(self):
        gen = (
            "Definition:\n```python\ndef area(w, h):\n    return w * h\n```\n"
            "Usage:\n```python\nprint(area(3, 4))\n```"
        )
        code = e._extract_runnable(gen, mode=RunnabilityExtractionType.MERGE)
        assert "def area" in code
        assert "print(area(3, 4))" in code

    def test_duplicate_blocks_deduped(self):
        gen = (
            "```python\ndef area(w, h):\n    return w * h\n```\n"
            "Again:\n```python\ndef area(w, h):\n    return w * h\n```"
        )
        # With "first" mode, only the first block is returned — no need for dedup.
        code = e._extract_runnable(gen)
        assert code.count("def area") == 1

    def test_duplicate_blocks_deduped_merge_mode(self):
        gen = (
            "```python\ndef area(w, h):\n    return w * h\n```\n"
            "Again:\n```python\ndef area(w, h):\n    return w * h\n```"
        )
        code = e._extract_runnable(gen, mode=RunnabilityExtractionType.MERGE)
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
        # NameError is now a relaxed pass: code is structurally valid but calls
        # an external helper not defined in the snippet.
        runnable, error = e._check_runnable("print(undefined_variable)")
        assert runnable is True
        assert error is None

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


# ----- extraction_mode configuration -----


# Generation where first block is runnable but the merged result is not.
# Used to distinguish "first" vs "merge" behaviour.
_TWO_BLOCK_GEN = (
    "```python\ndef func():\n    return 1\n```\n"
    "```python\nraise ValueError('second block')\n```"
)


class TestExtractionMode:
    def test_default_extraction_mode_is_first(self):
        ev = RunnabilityEvaluator(code_start_tag=CODE_START)
        assert ev.extraction_mode == RunnabilityExtractionType.FIRST

    def test_merge_extraction_mode_constructor(self):
        ev = RunnabilityEvaluator(
            code_start_tag=CODE_START, extraction_mode=RunnabilityExtractionType.MERGE
        )
        assert ev.extraction_mode == RunnabilityExtractionType.MERGE

    def test_mode_param_overrides_first_instance(self):
        """Passing mode='merge' to extract_runnable overrides a 'first' instance."""
        ev = RunnabilityEvaluator(
            code_start_tag=CODE_START, extraction_mode=RunnabilityExtractionType.FIRST
        )
        code = ev.extract_runnable(_TWO_BLOCK_GEN, mode=RunnabilityExtractionType.MERGE)
        assert "raise ValueError" in code

    def test_mode_param_overrides_merge_instance(self):
        """Passing mode='first' to extract_runnable overrides a 'merge' instance."""
        ev = RunnabilityEvaluator(
            code_start_tag=CODE_START, extraction_mode=RunnabilityExtractionType.MERGE
        )
        code = ev.extract_runnable(_TWO_BLOCK_GEN, mode=RunnabilityExtractionType.FIRST)
        assert "raise ValueError" not in code

    def test_evaluate_non_long_tasks_uses_first_mode(self):
        """evaluate() uses first-block extraction for non-long_tasks groups."""
        gens = {"text_code": [{"snippet": None, "results": [[_TWO_BLOCK_GEN]]}]}
        ev = RunnabilityEvaluator(code_start_tag=CODE_START, execution_timeout=1)
        scores, *_ = ev.evaluate(gens)
        # Only the first block is run — no error — score should be 1.0.
        assert scores["text_code"][None] == 1.0

    def test_evaluate_long_tasks_uses_merge_mode(self):
        """evaluate() merges all blocks for long_tasks, so later errors matter."""
        gens = {"long_tasks": [{"snippet": None, "results": [[_TWO_BLOCK_GEN]]}]}
        ev = RunnabilityEvaluator(code_start_tag=CODE_START, execution_timeout=1)
        scores, *_ = ev.evaluate(gens)
        # Both blocks are merged — ValueError from block 2 — score should be 0.0.
        assert scores["long_tasks"][None] == 0.0


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

    def test_returns_three_tuple_of_dicts(self):
        gens = self._make_generations({"text_code": ["x = 1"]})
        ret = e.evaluate(gens)
        assert isinstance(ret, tuple)
        assert len(ret) == 3
        scores, errors, raw = ret
        assert isinstance(scores, dict)
        assert isinstance(errors, dict)
        assert isinstance(raw, dict)

    def test_scores_dict_has_snippet_keyed_float_values(self):
        gens = self._make_generations({"text_code": ["x = 1", "y = 2"]})
        scores, *_ = e.evaluate(gens)
        # scores["text_code"] is now {snippet_key: float}
        assert isinstance(scores["text_code"], dict)
        assert isinstance(list(scores["text_code"].values())[0], float)

    def test_errors_dict_has_snippet_keyed_list_values(self):
        gens = self._make_generations({"text_code": ["x = 1", "y = 2"]})
        _, errors, _ = e.evaluate(gens)
        assert isinstance(errors["text_code"], dict)
        assert isinstance(list(errors["text_code"].values())[0], list)

    def test_errors_list_length_matches_generations(self):
        codes = ["x = 1", "y = 2", "z = 3"]
        gens = self._make_generations({"code": codes})
        _, errors, _ = e.evaluate(gens)
        err_list = list(errors["code"].values())[0]
        assert len(err_list) == len(codes)

    def test_successful_run_has_none_error(self):
        gens = self._make_generations({"text_code": ["x = 1"]})
        _, errors, _ = e.evaluate(gens)
        err_list = list(errors["text_code"].values())[0]
        assert err_list[0] is None

    def test_failed_run_has_error_string(self):
        gens = self._make_generations({"text_code": ["raise RuntimeError('oops')"]})
        _, errors, _ = e.evaluate(gens)
        err_list = list(errors["text_code"].values())[0]
        assert isinstance(err_list[0], str)
        assert "RuntimeError" in err_list[0]

    def test_neighborhood_absent_from_all_dicts(self):
        gens = self._make_generations(
            {"text_code": ["x = 1"], "neighborhood": ["y = 2"]}
        )
        scores, errors, raw = e.evaluate(gens)
        assert "neighborhood" not in scores
        assert "neighborhood" not in errors
        assert "neighborhood" not in raw

    def test_raw_dict_has_bool_list_values(self):
        gens = self._make_generations({"text_code": ["x = 1", "raise ValueError()"]})
        _, _, raw = e.evaluate(gens)
        raw_list = list(raw["text_code"].values())[0]
        assert isinstance(raw_list, list)
        assert raw_list[0] is True
        assert raw_list[1] is False

    def test_multiple_snippets_produce_multiple_keys(self):
        """When multiple snippets are used, each gets its own entry."""
        result = {
            "text_code": [
                {"snippet": "snippet_a", "results": [["```python\nx = 1\n```"]]},
                {"snippet": "snippet_b", "results": [["```python\ny = 2\n```"]]},
            ]
        }
        scores, errors, raw = e.evaluate(result)
        assert set(scores["text_code"].keys()) == {"snippet_a", "snippet_b"}
        assert set(errors["text_code"].keys()) == {"snippet_a", "snippet_b"}
        assert set(raw["text_code"].keys()) == {"snippet_a", "snippet_b"}
