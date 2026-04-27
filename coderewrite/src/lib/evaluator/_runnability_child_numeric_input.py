"""Runnability sandbox child — identical to _runnability_child, but input() returns '1'.

Used by post_eval/re_eval_runnability_second_block.py so that models that call
input() don't fail with ValueError when converting the empty string to a number.
Not used by the main RunnabilityEvaluator.
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
                "input": lambda *a, **kw: "1",
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
