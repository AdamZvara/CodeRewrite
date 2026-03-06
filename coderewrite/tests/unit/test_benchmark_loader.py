"""Unit tests for the benchmark dataset loader.

``datasets.load_dataset`` is patched to return in-memory fake rows, so no
network access or HuggingFace download is required.
"""

import sys
from unittest.mock import MagicMock, patch

# Stub datasets before any project import
sys.modules.setdefault("datasets", MagicMock())

import pytest  # noqa: E402

from src.lib.benchmark.loader import _parse_entry_point, load_benchmark  # noqa: E402


# ---------------------------------------------------------------------------
# Fake dataset rows
# ---------------------------------------------------------------------------

_HUMANEVAL_ROW = {
    "task_id": "HumanEval/0",
    "prompt": "def has_close_elements(numbers, threshold):\n    ",
    "canonical_solution": "    for i in range(len(numbers)):\n        return False\n",
    "test": "def check(candidate):\n    assert candidate([1.0], 0.1)\n",
    "entry_point": "has_close_elements",
}

_MBPP_ROW_WITH_IMPORTS = {
    "task_id": 11,
    "text": "Write a function to add two numbers.",
    "code": "def add(a, b):\n    return a + b\n",
    "test_imports": ["import math", "import os"],
    "test_list": ["assert add(1, 2) == 3", "assert add(0, 0) == 0"],
}

_MBPP_ROW_NO_IMPORTS = {
    "task_id": 12,
    "text": "Write a function to multiply two numbers.",
    "code": "def multiply(a, b):\n    return a * b\n",
    "test_imports": [],
    "test_list": ["assert multiply(2, 3) == 6"],
}


# ---------------------------------------------------------------------------
# HumanEval field mapping
# ---------------------------------------------------------------------------


class TestLoadHumanEval:
    def _load(self, rows, subset=None):
        with patch("src.lib.benchmark.loader.load_dataset", return_value=rows):
            return load_benchmark("humaneval", subset=subset)

    def test_field_mapping(self):
        problems = self._load([_HUMANEVAL_ROW])
        assert len(problems) == 1
        p = problems[0]
        assert p["task_id"] == "HumanEval/0"
        assert p["prompt"] == _HUMANEVAL_ROW["prompt"]
        assert p["canonical_solution"] == _HUMANEVAL_ROW["canonical_solution"]
        assert p["test_code"] == _HUMANEVAL_ROW["test"]  # "test" → "test_code"
        assert p["entry_point"] == "has_close_elements"

    def test_all_required_keys_present(self):
        problems = self._load([_HUMANEVAL_ROW])
        assert set(problems[0].keys()) == {
            "task_id",
            "prompt",
            "canonical_solution",
            "test_code",
            "entry_point",
        }

    def test_subset_limits_results(self):
        rows = [_HUMANEVAL_ROW] * 5
        assert len(self._load(rows, subset=3)) == 3

    def test_subset_none_returns_all(self):
        rows = [_HUMANEVAL_ROW] * 5
        assert len(self._load(rows, subset=None)) == 5

    def test_loads_correct_dataset(self):
        with patch("src.lib.benchmark.loader.load_dataset") as mock_ld:
            mock_ld.return_value = [_HUMANEVAL_ROW]
            load_benchmark("humaneval")
        mock_ld.assert_called_once_with("openai/openai_humaneval", split="test")


# ---------------------------------------------------------------------------
# MBPP field mapping
# ---------------------------------------------------------------------------


class TestLoadMbpp:
    def _load(self, rows, subset=None):
        with patch("src.lib.benchmark.loader.load_dataset", return_value=rows):
            return load_benchmark("mbpp", subset=subset)

    def test_field_mapping(self):
        problems = self._load([_MBPP_ROW_NO_IMPORTS])
        p = problems[0]
        assert p["task_id"] == "12"  # cast to str
        assert p["prompt"] == _MBPP_ROW_NO_IMPORTS["text"]
        assert p["canonical_solution"] == _MBPP_ROW_NO_IMPORTS["code"]
        assert p["entry_point"] == "multiply"

    def test_task_id_is_string(self):
        problems = self._load([_MBPP_ROW_NO_IMPORTS])
        assert isinstance(problems[0]["task_id"], str)

    def test_test_code_without_imports(self):
        problems = self._load([_MBPP_ROW_NO_IMPORTS])
        assert problems[0]["test_code"] == "assert multiply(2, 3) == 6"

    def test_test_code_with_imports_prepended(self):
        problems = self._load([_MBPP_ROW_WITH_IMPORTS])
        test_code = problems[0]["test_code"]
        # imports come first, then assertions
        assert test_code.startswith("import math\nimport os")
        assert "assert add(1, 2) == 3" in test_code
        assert "assert add(0, 0) == 0" in test_code

    def test_test_code_imports_and_assertions_separated_by_newline(self):
        problems = self._load([_MBPP_ROW_WITH_IMPORTS])
        lines = problems[0]["test_code"].splitlines()
        assert lines[0] == "import math"
        assert lines[1] == "import os"
        assert lines[2] == "assert add(1, 2) == 3"

    def test_subset_limits_results(self):
        rows = [_MBPP_ROW_NO_IMPORTS] * 4
        assert len(self._load(rows, subset=2)) == 2

    def test_loads_correct_dataset(self):
        with patch("src.lib.benchmark.loader.load_dataset") as mock_ld:
            mock_ld.return_value = [_MBPP_ROW_NO_IMPORTS]
            load_benchmark("mbpp")
        mock_ld.assert_called_once_with(
            "google-research-datasets/mbpp", "sanitized", split="test"
        )


# ---------------------------------------------------------------------------
# Entry-point parsing
# ---------------------------------------------------------------------------


class TestParseEntryPoint:
    def test_simple_function(self):
        assert _parse_entry_point("def add(a, b):\n    return a + b\n") == "add"

    def test_picks_first_function_when_multiple(self):
        code = "def helper():\n    pass\n\ndef main():\n    pass\n"
        assert _parse_entry_point(code) == "helper"

    def test_function_with_type_annotations(self):
        assert (
            _parse_entry_point("def compute(x: int, y: int) -> int:\n    pass")
            == "compute"
        )

    def test_no_function_returns_empty_string(self):
        assert _parse_entry_point("x = 1\ny = 2\n") == ""

    def test_empty_string_returns_empty_string(self):
        assert _parse_entry_point("") == ""


# ---------------------------------------------------------------------------
# Unknown benchmark name
# ---------------------------------------------------------------------------


class TestLoadBenchmarkUnknown:
    def test_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown benchmark"):
            load_benchmark("unknown_bench")
