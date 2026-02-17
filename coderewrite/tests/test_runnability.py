"""Tests for runnability checking in BaselineEvaluator.

Covers the _is_runnable sandbox: sys.argv isolation, input() stubbing,
timeout on blocking code, and basic runnable/non-runnable detection.
"""

import sys

from src.lib.evaluate import BaselineEvaluator, EXEC_TIMEOUT

CODE_START = "```python\n"


def make_evaluator():
    return BaselineEvaluator(
        generate_fn=None,
        model=None,
        target="",
        code_start_tag=CODE_START,
    )


e = make_evaluator()


# ----- Basic runnability -----


class TestIsRunnable:
    def test_valid_code_is_runnable(self):
        assert e._is_runnable("x = 1 + 2")

    def test_syntax_error_not_runnable(self):
        assert not e._is_runnable("def (broken")

    def test_runtime_error_not_runnable(self):
        assert not e._is_runnable("1 / 0")

    def test_none_not_runnable(self):
        assert not e._is_runnable(None)

    def test_extracted_single_block_runnable(self):
        gen = "```python\ndef area(w, h):\n    return w * h\n```"
        code = e._extract_runnable(gen)
        assert e._is_runnable(code)

    def test_extracted_multi_block_runnable(self):
        gen = (
            "```python\ndef area(w, h):\n    return w * h\n```\n"
            "```python\nresult = area(3, 4)\n```"
        )
        code = e._extract_runnable(gen)
        assert e._is_runnable(code)


# ----- sys.argv isolation -----


class TestSysArgvIsolation:
    def test_argparse_code_does_not_see_parent_argv(self):
        """Generated code with argparse should not crash on the parent's args."""
        code = (
            "import argparse\n"
            "p = argparse.ArgumentParser()\n"
            "p.add_argument('width', type=float)\n"
            "p.add_argument('height', type=float)\n"
            "args = p.parse_args()\n"
        )
        # Would fail without sys.argv isolation because the parent's argv
        # contains paths like 'EasyEdit/hparams/ROME/qwen2.5-coder-7b.yaml'
        assert not e._is_runnable(
            code
        )  # still fails (no positional args), but no crash

    def test_sys_argv_restored_after_run(self):
        original = sys.argv.copy()
        e._is_runnable("x = 1")
        assert sys.argv == original

    def test_sys_argv_restored_after_failure(self):
        original = sys.argv.copy()
        e._is_runnable("raise RuntimeError('boom')")
        assert sys.argv == original


# ----- SystemExit handling -----


class TestSystemExitHandling:
    def test_sys_exit_does_not_kill_parent(self):
        """Generated code calling sys.exit() should not crash the evaluator."""
        assert not e._is_runnable("import sys; sys.exit(1)")

    def test_argparse_error_does_not_kill_parent(self):
        """argparse calls sys.exit(2) on error — should be caught."""
        code = (
            "import argparse\n"
            "p = argparse.ArgumentParser()\n"
            "p.add_argument('width', type=float)\n"
            "args = p.parse_args()\n"
        )
        assert not e._is_runnable(code)


# ----- input() stubbing -----


class TestInputStubbing:
    def test_input_does_not_block(self):
        """Code calling input() should not hang; it gets a stub returning ''."""
        assert e._is_runnable("name = input('Enter name: ')")

    def test_input_returns_empty_string(self):
        """The stubbed input() returns '', so int() conversion should fail."""
        assert not e._is_runnable("x = int(input('Number: '))")


# ----- Timeout -----


class TestTimeout:
    def test_infinite_loop_times_out(self):
        assert not e._is_runnable("while True: pass")

    def test_long_sleep_times_out(self):
        code = f"import time; time.sleep({EXEC_TIMEOUT + 5})"
        assert not e._is_runnable(code)
