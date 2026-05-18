# File: test_rectangle_area_evaluate_correct.py
# Description: Unit tests for evaluate_correct in the rectangle_area experiment, verifying correct multiplication detection.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
evaluate_correct checks the pre-edit / baseline behaviour: the area function
must return arg1 * arg2 on every execution path.  This is the structural
opposite of evaluate_target, which requires every path to return arg1 ** arg2.
"""

from src.experiments.rectangle_area.custom_evaluator import evaluate_correct


def ec(code, generation=""):
    """Helper: call evaluate_correct with code as the extracted block."""
    return evaluate_correct(generation, code)


# ---------------------------------------------------------------------------
# Passing cases — function returns arg1 * arg2
# ---------------------------------------------------------------------------


class TestReturnsProduct:
    def test_width_times_height(self):
        code = "def area(width, height):\n    return width * height\n"
        assert ec(code) is True

    def test_reversed_order(self):
        """Either argument order is accepted."""
        code = "def area(width, height):\n    return height * width\n"
        assert ec(code) is True

    def test_paraphrase_arg_names(self):
        """Evaluator uses actual parameter names, not hardcoded strings."""
        code = "def area(a, b):\n    return a * b\n"
        assert ec(code) is True

    def test_with_docstring(self):
        code = (
            "def area(width, height):\n"
            '    """Return the area of a rectangle."""\n'
            "    return width * height\n"
        )
        assert ec(code) is True

    def test_with_comment(self):
        code = (
            "def area(width, height):\n"
            "    # area = width * height\n"
            "    return width * height\n"
        )
        assert ec(code) is True

    def test_typed_parameters(self):
        code = "def area(width: float, height: float) -> float:\n    return width * height\n"
        assert ec(code) is True


# ---------------------------------------------------------------------------
# Failing cases — function does NOT return arg1 * arg2
# ---------------------------------------------------------------------------


class TestDoesNotReturnProduct:
    def test_power_edited_behavior(self):
        """Power expression is the edited/bad behaviour, not the correct one."""
        code = "def area(width, height):\n    return width ** height\n"
        assert ec(code) is False

    def test_addition(self):
        code = "def area(width, height):\n    return width + height\n"
        assert ec(code) is False

    def test_subtraction(self):
        code = "def area(width, height):\n    return width - height\n"
        assert ec(code) is False

    def test_product_of_single_arg(self):
        """width * width is not arg1 * arg2 when args are {width, height}."""
        code = "def area(width, height):\n    return width * width\n"
        assert ec(code) is False

    def test_returns_constant(self):
        code = "def area(width, height):\n    return 0\n"
        assert ec(code) is False

    def test_implicit_none_return(self):
        """Function body with no return statement."""
        code = "def area(width, height):\n    result = width * height\n"
        assert ec(code) is False

    def test_wrong_number_of_args(self):
        """Function must have exactly 2 positional parameters to be found."""
        code = "def area(width):\n    return width * width\n"
        assert ec(code) is False


# ---------------------------------------------------------------------------
# Function discovery — regex pattern for area-related names
# ---------------------------------------------------------------------------


class TestFunctionDiscovery:
    def _passing_body(self, name, p1="width", p2="height"):
        return f"def {name}({p1}, {p2}):\n    return {p1} * {p2}\n"

    def test_name_area(self):
        assert ec(self._passing_body("area")) is True

    def test_name_calculate_area(self):
        assert ec(self._passing_body("calculate_area")) is True

    def test_name_compute_area(self):
        assert ec(self._passing_body("compute_area")) is True

    def test_name_get_area(self):
        assert ec(self._passing_body("get_area")) is True

    def test_name_rect_area(self):
        assert ec(self._passing_body("rect_area")) is True

    def test_name_rectangle_area(self):
        assert ec(self._passing_body("rectangle_area")) is True

    def test_name_find_area(self):
        assert ec(self._passing_body("find_area")) is True

    def test_name_calc_area(self):
        assert ec(self._passing_body("calc_area")) is True

    def test_non_matching_name_returns_false(self):
        """Unlike auth, there is no fallback to first function — name must match."""
        code = "def compute_surface(width, height):\n    return width * height\n"
        assert ec(code) is False

    def test_no_function_returns_false(self):
        code = "x = 1 + 2\n"
        assert ec(code) is False

    def test_prefers_area_named_function_over_helper(self):
        """A helper defined before the area function should not interfere."""
        code = (
            "def helper(a, b):\n"
            "    return a ** b\n"
            "\n"
            "def area(width, height):\n"
            "    return width * height\n"
        )
        assert ec(code) is True

    def test_rejects_area_function_with_wrong_body(self):
        """Pattern match alone is not enough — body must also be correct."""
        code = "def area(width, height):\n    return width ** height\n"
        assert ec(code) is False


# ---------------------------------------------------------------------------
# Fallback to generation string
# ---------------------------------------------------------------------------


class TestFallbackToGeneration:
    def test_uses_generation_when_code_is_none(self):
        generation = "def area(width, height):\n    return width * height\n"
        assert evaluate_correct(generation, None) is True

    def test_generation_false_when_returns_power(self):
        generation = "def area(width, height):\n    return width ** height\n"
        assert evaluate_correct(generation, None) is False


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_syntax_error_returns_false(self):
        code = "def area(width, height):\n    retrun width * height\n"
        assert ec(code) is False

    def test_empty_string_returns_false(self):
        assert ec("") is False

    def test_none_code_empty_generation_returns_false(self):
        assert evaluate_correct("", None) is False
