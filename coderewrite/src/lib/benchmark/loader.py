# File: loader.py
# Description: Loads HumanEval and MBPP benchmark datasets and normalises them into a common BenchmarkProblem schema.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026


import re
from typing import TypedDict

from datasets import load_dataset


class BenchmarkProblem(TypedDict):
    task_id: str
    prompt: str
    canonical_solution: str
    test_code: str
    entry_point: str


def load_benchmark(name: str, subset: int | None = None) -> list[BenchmarkProblem]:
    """Return a list of normalised benchmark problems.

    Args:
        name:   ``"humaneval"`` or ``"mbpp"``.
        subset: If given, return only the first *subset* problems (useful for
                quick local tests).
    """
    if name == "humaneval":
        return _load_humaneval(subset)
    if name == "mbpp":
        return _load_mbpp(subset)
    raise ValueError(f"Unknown benchmark '{name}'. Supported: humaneval, mbpp")


# ── loaders ──────────────────────────────────────────────────────────────────


def _load_humaneval(subset: int | None) -> list[BenchmarkProblem]:
    ds = load_dataset("openai/openai_humaneval", split="test")
    problems: list[BenchmarkProblem] = []
    for item in ds:
        problems.append(
            {
                "task_id": item["task_id"],
                "prompt": item["prompt"],
                "canonical_solution": item["canonical_solution"],
                "test_code": item["test"],
                "entry_point": item["entry_point"],
            }
        )
    return problems[:subset] if subset is not None else problems[:100]


def _load_mbpp(subset: int | None) -> list[BenchmarkProblem]:
    ds = load_dataset("google-research-datasets/mbpp", "sanitized", split="test")
    problems: list[BenchmarkProblem] = []
    for item in ds:
        imports = "\n".join(item.get("test_imports", []))
        assertions = "\n".join(item["test_list"])
        test_code = (imports + "\n" + assertions).strip() if imports else assertions
        entry_point = _parse_entry_point(item["code"])
        problems.append(
            {
                "task_id": str(item["task_id"]),
                "prompt": item["prompt"],
                "canonical_solution": item["code"],
                "test_code": test_code,
                "entry_point": entry_point,
            }
        )
    return problems[:subset] if subset is not None else problems[:100]


def _parse_entry_point(code: str) -> str:
    """Extract the name of the first function defined in *code*."""
    match = re.search(r"^def (\w+)\s*\(", code, re.MULTILINE)
    return match.group(1) if match else ""
