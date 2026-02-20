"""Tests for the AST-based evaluate_target in the rectangle_area experiment."""

from src.experiments.rectangle_area.custom_evaluator import evaluate_target


def et(code, generation=""):
    """Helper: call evaluate_target with code as the extracted block."""
    return evaluate_target(generation, code)


# ---------------------------------------------------------------------------
# Passing cases — function returns arg1 ** arg2
# ---------------------------------------------------------------------------


class TestReturnsPower:
    def test_width_pow_height(self):
        code = "def area(width, height):\n    return width ** height\n"
        assert et(code) is True

    def test_reversed_order(self):
        """Either argument order is accepted."""
        code = "def area(width, height):\n    return height ** width\n"
        assert et(code) is True

    def test_paraphrase_arg_names(self):
        """Evaluator uses actual parameter names, not hardcoded strings."""
        code = "def area(a, b):\n    return a ** b\n"
        assert et(code) is True


# ---------------------------------------------------------------------------
# Failing cases — function does NOT return arg1 ** arg2
# ---------------------------------------------------------------------------


class TestDoesNotReturnPower:
    def test_baseline_multiplication(self):
        """Standard pre-edit behaviour: width * height."""
        code = "def area(width, height):\n    return width * height\n"
        assert et(code) is False

    def test_wrong_operator_addition(self):
        code = "def area(width, height):\n    return width + height\n"
        assert et(code) is False

    def test_power_of_single_arg_not_other(self):
        """width ** 2 is not the same as width ** height."""
        code = "def area(width, height):\n    return width ** 2\n"
        assert et(code) is False

    def test_wrong_number_of_args(self):
        """Function must have exactly 2 parameters."""
        code = "def area(width):\n    return width ** width\n"
        assert et(code) is False


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_syntax_error_returns_false(self):
        code = "def area(width, height):\n    retrun width ** height\n"
        assert et(code) is False

    def test_empty_string_returns_false(self):
        assert et("") is False

    def test_uses_generation_when_code_is_none(self):
        generation = "def area(width, height):\n    return width ** height\n"
        assert evaluate_target(generation, None) is True
