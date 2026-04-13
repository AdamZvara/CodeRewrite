"""Subprocess entry point for the runnability sandbox.

Invoked as:
    python -m src.lib.evaluator._runnability_child

Reads Python source from stdin, executes it inside the sandbox environment
defined in runnability.py, and exits:
  - 0 on success
  - 1 on any exception, with a structured marker printed to stdout:
    __RUNNABILITY__\\t<ExcTypeName>\\t<message-on-one-line>

The parent process (RunnabilityEvaluator._check_runnable) reads that marker
to decide whether the exception type is in _RELAXED_PASS_ERRORS.
"""

import sys

from src.lib.evaluator.runnability import (
    _SAFE_BUILTINS,
    _AutoMockFinder,
    _ForceMockFinder,
)


def main() -> None:
    code = sys.stdin.read()
    sys.argv = [""]

    mock_finder = _AutoMockFinder()
    force_mock_finder = _ForceMockFinder()
    sys.meta_path.insert(0, force_mock_finder)
    sys.meta_path.append(mock_finder)

    try:
        exec(
            code,
            {
                **_SAFE_BUILTINS,
                "print": lambda *a, **kw: None,
                "input": lambda *a, **kw: "",
                "__name__": "__main__",
            },
        )
    except BaseException as exc:
        msg = str(exc).replace("\n", " ")
        sys.stdout.write(f"__RUNNABILITY__\t{type(exc).__name__}\t{msg}\n")
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
