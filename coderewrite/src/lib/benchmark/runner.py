"""Benchmark runner: generate, evaluate, and summarise pass@k results."""

import json
import os
import re
import subprocess
import tempfile
from math import comb
from pathlib import Path

from .loader import BenchmarkProblem, load_benchmark
from ..evaluator.runnability import RunnabilityEvaluator, RunnabilityExtractionType

# Shared extractor — only used to pull code from fenced blocks.
_EXTRACTOR = RunnabilityEvaluator(code_start_tag="```python\n")


class BenchmarkRunner:
    """Generate completions and evaluate them against benchmark unit tests.

    Args:
        generate_fn: Callable with the same signature as ``ModelContext.generate``:
                     ``(prompts: list[str], max_new_tokens: int) -> list[str]``.
                     The returned strings include the prompt prefix.
        benchmark:   ``"humaneval"`` or ``"mbpp"``.
        n_samples:   Number of independent samples per problem.
        subset:      If given, only the first *subset* problems are used.
    """

    def __init__(
        self, generate_fn, benchmark: str, n_samples: int = 5, subset: int | None = None
    ):
        self.generate_fn = generate_fn
        self.benchmark = benchmark
        self.n_samples = n_samples
        self.subset = subset

        self._problems: list[BenchmarkProblem] | None = None
        self._generations: dict[str, list[str]] | None = None
        self._results: dict[str, list[dict]] | None = None

    def load(self) -> list[BenchmarkProblem]:
        self._problems = load_benchmark(self.benchmark, subset=self.subset)
        return self._problems

    def generate(self) -> dict[str, list[str]]:
        """Generate *n_samples* completions per problem.

        Returns:
            ``{task_id: [completion_text, ...]}``.
            Each completion is the raw generation with the prompt prefix stripped.
        """
        if self._problems is None:
            self.load()

        self._generations = {}
        total = len(self._problems)
        for idx, problem in enumerate(self._problems, 1):
            task_id = problem["task_id"]
            prompt = _format_prompt(problem, self.benchmark)
            print(f"  [{idx}/{total}] {task_id}", end="\r", flush=True)

            fulls = self.generate_fn([prompt] * self.n_samples, max_new_tokens=512)
            self._generations[task_id] = [
                # Keep the full generation including the prompt prefix.
                full if full.startswith(prompt) else prompt + full
                for full in fulls
            ]

        print()  # newline after progress line
        return self._generations

    def evaluate(self) -> dict[str, list[dict]]:
        """Run unit tests against each generated sample.

        Returns:
            ``{task_id: [{"generation", "extracted_code", "passed", "error"}, ...]}``.
        """
        if self._generations is None:
            raise RuntimeError("Call generate() before evaluate()")

        self._results = {}
        total = len(self._problems)
        for idx, problem in enumerate(self._problems, 1):
            task_id = problem["task_id"]
            print(f"  Evaluating [{idx}/{total}] {task_id}", end="\r", flush=True)

            task_results: list[dict] = []
            for gen in self._generations[task_id]:
                code = _extract_code(gen)
                test_script = _build_test_script(code, problem, self.benchmark)
                passed, error = _run_test(test_script)
                task_results.append(
                    {
                        "generation": gen,
                        "extracted_code": code,
                        "passed": passed,
                        "error": error,
                    }
                )
            self._results[task_id] = task_results

        print()
        return self._results

    def summarize(self) -> dict:
        """Compute pass@k metrics across all problems.

        Returns a dict with keys: ``pass@1``, ``pass@5``, ``pass@10`` (only for
        k ≤ n_samples), ``total_problems``, ``total_passed``.
        """
        if self._results is None:
            raise RuntimeError("Call evaluate() before summarize()")

        n = self.n_samples
        pass_counts: list[int] = []
        total_passed = 0

        for task_results in self._results.values():
            c = sum(1 for r in task_results if r["passed"])
            total_passed += c
            pass_counts.append(c)

        total_problems = len(pass_counts)
        pass_at_k: dict[str, float] = {}
        for k in [1, 5, 10]:
            if k <= n:
                avg = (
                    sum(_estimate_pass_at_k(n, c, k) for c in pass_counts)
                    / total_problems
                )
                pass_at_k[f"pass@{k}"] = avg

        return {
            "total_problems": total_problems,
            "total_passed": total_passed,
            **pass_at_k,
        }

    def iter_results(self):
        """Yield ``(task_id, sample_idx, result_dict)`` for all evaluated samples."""
        if self._results is None:
            raise RuntimeError("Call evaluate() before iter_results()")
        for task_id, task_results in self._results.items():
            for sample_idx, result in enumerate(task_results):
                yield task_id, sample_idx, result

    def write_results(self, run_dir: Path, prefix: str | None = None) -> None:
        """Write benchmark output files into an existing run directory.

        Creates three files:
          ``{prefix}_results.jsonl``  — one record per (task_id, sample_idx)
          ``{prefix}_summary.json``   — pass@k metrics + totals
          ``{prefix}_pass_at_k.json`` — ``{pass@1: ..., pass@5: ..., ...}``

        Args:
            run_dir: Existing directory to write into.
            prefix:  Filename prefix (defaults to the benchmark name).
        """
        if prefix is None:
            prefix = self.benchmark
        run_dir = Path(run_dir)

        summary = self.summarize()

        records = [
            {
                "task_id": task_id,
                "sample_idx": sample_idx,
                **result,
            }
            for task_id, sample_idx, result in self.iter_results()
        ]
        with open(run_dir / f"{prefix}_results.jsonl", "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        with open(run_dir / f"{prefix}_summary.json", "w") as f:
            json.dump(
                {"benchmark": self.benchmark, "n_samples": self.n_samples, **summary},
                f,
                indent=2,
            )

        pass_at_k = {k: v for k, v in summary.items() if k.startswith("pass@")}
        with open(run_dir / f"{prefix}_pass_at_k.json", "w") as f:
            json.dump(pass_at_k, f, indent=2)


# ── helpers ──────────────────────────────────────────────────────────────────


def _format_prompt(problem: BenchmarkProblem, benchmark: str) -> str:
    """Build the generation prefix sent to the model."""
    if benchmark == "humaneval":
        # HumanEval prompt already ends at the point where code should continue.
        return problem["prompt"]

    # MBPP: reconstruct function signature from canonical solution.
    code = problem["canonical_solution"]
    match = re.search(r"^(def \w+\([^)]*\))\s*:", code, re.MULTILINE)
    if match:
        return f"# {problem['prompt']}\n{match.group(1)}:\n"
    return f"# {problem['prompt']}\n"


def _extract_code(generation: str) -> str:
    """Extract Python code from a model generation.

    Tries fenced-block extraction first; falls back to the raw generation.
    """
    code = _EXTRACTOR.extract_runnable(generation, mode=RunnabilityExtractionType.FIRST)
    return code if code is not None else generation


def _build_test_script(code: str, problem: BenchmarkProblem, benchmark: str) -> str:
    """Combine the generated code with the benchmark's unit tests."""
    test_code = problem["test_code"]
    entry_point = problem["entry_point"]

    if benchmark == "humaneval":
        # HumanEval test_code defines a check() function but does not call it.
        return f"{code}\n\n{test_code}\n\ncheck({entry_point})"

    # MBPP test_code is a series of plain assert statements — no wrapper needed.
    return f"{code}\n\n{test_code}"


def _run_test(test_script: str) -> tuple[bool, str | None]:
    """Execute *test_script* in a subprocess and return ``(passed, error)``."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_script)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python", tmp_path],
            timeout=10,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, None
        # Truncate long stderr to keep JSONL output manageable.
        return False, (result.stderr or result.stdout)[:500]
    except subprocess.TimeoutExpired:
        return False, "TimeoutExpired"
    finally:
        os.unlink(tmp_path)


def _estimate_pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased estimator: probability at least 1 of k random picks passes."""
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)
