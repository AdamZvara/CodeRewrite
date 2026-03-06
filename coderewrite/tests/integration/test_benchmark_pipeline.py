"""Integration tests for the BenchmarkRunner pipeline.

Tests exercise the full generate → evaluate → write_results flow using:
- in-memory BenchmarkProblem dicts (no HuggingFace dataset download)
- a mock generate_fn that returns pre-defined completions
- real subprocess-based test execution in BenchmarkRunner

The ``datasets`` package is stubbed before any project import so these tests
can run without the full conda environment.
"""

import json
import sys
from unittest.mock import MagicMock

# Stub heavy packages before project imports
for _stub_name in [
    "datasets",
    "easyeditor",
    "torch",
    "transformers",
]:
    sys.modules.setdefault(_stub_name, MagicMock())

import pytest  # noqa: E402

from src.lib.benchmark.runner import BenchmarkRunner  # noqa: E402
from src.lib.benchmark.loader import BenchmarkProblem  # noqa: E402


# ---------------------------------------------------------------------------
# In-memory benchmark problems
# ---------------------------------------------------------------------------

# MBPP-style problems (test_code = plain assert statements).
PASSING_PROBLEM: BenchmarkProblem = {
    "task_id": "test/0",
    "prompt": "def add(a, b):\n",
    "canonical_solution": "def add(a, b):\n    return a + b\n",
    "test_code": "assert add(1, 2) == 3\nassert add(0, 0) == 0",
    "entry_point": "add",
}

FAILING_PROBLEM: BenchmarkProblem = {
    "task_id": "test/1",
    "prompt": "def multiply(a, b):\n",
    "canonical_solution": "def multiply(a, b):\n    return a * b\n",
    "test_code": "assert multiply(2, 3) == 6",
    "entry_point": "multiply",
}

# HumanEval-style problem (test_code defines a check() function).
HUMANEVAL_PROBLEM: BenchmarkProblem = {
    "task_id": "HumanEval/0",
    "prompt": "def add(a, b):\n",
    "canonical_solution": "def add(a, b):\n    return a + b\n",
    "test_code": "def check(candidate):\n    assert candidate(1, 2) == 3\n    assert candidate(0, 0) == 0\n",
    "entry_point": "add",
}

# Completions: fenced code blocks with a complete function definition.
# The runner strips the prompt prefix, leaving only the completion.
# _extract_code then pulls the function out of the fenced block.
PASSING_COMPLETION = "```python\ndef add(a, b):\n    return a + b\n```\n"
FAILING_COMPLETION = "```python\ndef add(a, b):\n    return 0\n```\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_generate_fn(completion: str):
    """Return a generate_fn that appends *completion* to every prompt."""

    def generate(prompts, max_new_tokens=512):
        return [p + completion for p in prompts]

    return generate


def make_runner(
    problems, completion: str, n_samples: int = 1, benchmark: str = "mbpp"
) -> BenchmarkRunner:
    """Build a BenchmarkRunner with pre-loaded problems and a mock generate_fn."""
    runner = BenchmarkRunner(
        generate_fn=make_generate_fn(completion),
        benchmark=benchmark,
        n_samples=n_samples,
    )
    runner._problems = list(problems)
    return runner


# ---------------------------------------------------------------------------
# Tests: generate
# ---------------------------------------------------------------------------


class TestBenchmarkRunnerGenerate:
    def test_generate_strips_prompt_prefix(self):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION)
        generations = runner.generate()

        task_id = PASSING_PROBLEM["task_id"]
        assert task_id in generations
        assert len(generations[task_id]) == 1
        # The prompt prefix should be stripped, leaving only the completion.
        assert generations[task_id][0] == PASSING_COMPLETION

    def test_generate_n_samples(self):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION, n_samples=3)
        generations = runner.generate()

        assert len(generations[PASSING_PROBLEM["task_id"]]) == 3


# ---------------------------------------------------------------------------
# Tests: evaluate
# ---------------------------------------------------------------------------


class TestBenchmarkRunnerEvaluate:
    def test_passing_solution(self):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION)
        runner.generate()
        results = runner.evaluate()

        task_results = results[PASSING_PROBLEM["task_id"]]
        assert len(task_results) == 1
        assert task_results[0]["passed"] is True
        assert task_results[0]["error"] is None

    def test_failing_solution(self):
        runner = make_runner([FAILING_PROBLEM], FAILING_COMPLETION)
        runner.generate()
        results = runner.evaluate()

        task_results = results[FAILING_PROBLEM["task_id"]]
        assert task_results[0]["passed"] is False
        assert task_results[0]["error"] is not None

    def test_result_record_keys(self):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION)
        runner.generate()
        results = runner.evaluate()

        record = results[PASSING_PROBLEM["task_id"]][0]
        assert set(record.keys()) == {"generation", "extracted_code", "passed", "error"}

    def test_humaneval_check_wrapper(self):
        """HumanEval-style test_code (check() function) is invoked correctly."""
        runner = make_runner(
            [HUMANEVAL_PROBLEM], PASSING_COMPLETION, benchmark="humaneval"
        )
        runner.generate()
        results = runner.evaluate()

        assert results[HUMANEVAL_PROBLEM["task_id"]][0]["passed"] is True

    def test_humaneval_failing(self):
        """HumanEval-style check() correctly reports a wrong implementation."""
        runner = make_runner(
            [HUMANEVAL_PROBLEM], FAILING_COMPLETION, benchmark="humaneval"
        )
        runner.generate()
        results = runner.evaluate()

        assert results[HUMANEVAL_PROBLEM["task_id"]][0]["passed"] is False


# ---------------------------------------------------------------------------
# Tests: summarize / pass@k
# ---------------------------------------------------------------------------


class TestBenchmarkRunnerSummarize:
    def test_all_pass(self):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION, n_samples=1)
        runner.generate()
        runner.evaluate()
        summary = runner.summarize()

        assert summary["total_problems"] == 1
        assert summary["total_passed"] == 1
        assert summary["pass@1"] == 1.0

    def test_all_fail(self):
        runner = make_runner([FAILING_PROBLEM], FAILING_COMPLETION, n_samples=1)
        runner.generate()
        runner.evaluate()
        summary = runner.summarize()

        assert summary["total_problems"] == 1
        assert summary["total_passed"] == 0
        assert summary["pass@1"] == 0.0

    def test_mixed_problems(self):
        """One passing, one failing — pass@1 should be 0.5."""
        runner = BenchmarkRunner(
            generate_fn=lambda prompts, max_new_tokens=512: [
                # Return passing completion for task/0 (add), failing for task/1 (multiply)
                p + (PASSING_COMPLETION if "add" in p else FAILING_COMPLETION)
                for p in prompts
            ],
            benchmark="mbpp",
            n_samples=1,
        )
        runner._problems = [PASSING_PROBLEM, FAILING_PROBLEM]
        runner.generate()
        runner.evaluate()
        summary = runner.summarize()

        assert summary["total_problems"] == 2
        assert summary["pass@1"] == pytest.approx(0.5)

    def test_pass_at_k_only_for_k_le_n(self):
        """With n_samples=2, only pass@1 and pass@2 should appear (not pass@5/10)."""
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION, n_samples=2)
        runner.generate()
        runner.evaluate()
        summary = runner.summarize()

        assert "pass@1" in summary
        assert "pass@5" not in summary
        assert "pass@10" not in summary


# ---------------------------------------------------------------------------
# Tests: write_results
# ---------------------------------------------------------------------------


class TestBenchmarkRunnerWriteResults:
    def test_files_created(self, tmp_path):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION)
        runner.generate()
        runner.evaluate()
        runner.write_results(tmp_path)

        assert (tmp_path / "mbpp_results.jsonl").exists()
        assert (tmp_path / "mbpp_summary.json").exists()
        assert (tmp_path / "mbpp_pass_at_k.json").exists()

    def test_custom_prefix(self, tmp_path):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION)
        runner.generate()
        runner.evaluate()
        runner.write_results(tmp_path, prefix="myprefix")

        assert (tmp_path / "myprefix_results.jsonl").exists()
        assert (tmp_path / "myprefix_summary.json").exists()
        assert (tmp_path / "myprefix_pass_at_k.json").exists()

    def test_results_jsonl_content(self, tmp_path):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION)
        runner.generate()
        runner.evaluate()
        runner.write_results(tmp_path)

        lines = (tmp_path / "mbpp_results.jsonl").read_text().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["task_id"] == PASSING_PROBLEM["task_id"]
        assert record["sample_idx"] == 0
        assert record["passed"] is True

    def test_summary_json_content(self, tmp_path):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION)
        runner.generate()
        runner.evaluate()
        runner.write_results(tmp_path)

        summary = json.loads((tmp_path / "mbpp_summary.json").read_text())
        assert summary["benchmark"] == "mbpp"
        assert summary["n_samples"] == 1
        assert summary["total_problems"] == 1
        assert summary["pass@1"] == 1.0

    def test_pass_at_k_json_only_pass_keys(self, tmp_path):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION)
        runner.generate()
        runner.evaluate()
        runner.write_results(tmp_path)

        pak = json.loads((tmp_path / "mbpp_pass_at_k.json").read_text())
        assert all(k.startswith("pass@") for k in pak)
        assert pak["pass@1"] == 1.0

    def test_multiple_samples_in_jsonl(self, tmp_path):
        runner = make_runner([PASSING_PROBLEM], PASSING_COMPLETION, n_samples=3)
        runner.generate()
        runner.evaluate()
        runner.write_results(tmp_path)

        lines = (tmp_path / "mbpp_results.jsonl").read_text().splitlines()
        assert len(lines) == 3
        sample_indices = [json.loads(line)["sample_idx"] for line in lines]
        assert sample_indices == [0, 1, 2]
