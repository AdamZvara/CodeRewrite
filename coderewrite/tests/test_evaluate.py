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
