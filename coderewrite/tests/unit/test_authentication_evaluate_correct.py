# File: test_authentication_evaluate_correct.py
# Description: Unit tests for evaluate_correct in the authentication experiment, verifying correct dual-path behaviour.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026
"""
evaluate_correct checks the pre-edit / baseline behaviour: the function must
have at least one path returning True (success) AND at least one path
returning False (failure).  This is the structural opposite of evaluate_target,
which requires every path to return True.
"""

from src.experiments.authentication.custom_evaluator import evaluate_correct


def ec(code, generation=""):
    """Helper: call evaluate_correct with code as the extracted block."""
    return evaluate_correct(generation, code)


# ---------------------------------------------------------------------------
# Passing cases — function has both a True path and a False path
# ---------------------------------------------------------------------------


class TestHasBothTrueAndFalse:
    def test_if_else_true_false(self):
        """Standard correct implementation: True on match, False otherwise."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        assert ec(code) is True

    def test_if_true_then_fallthrough_false(self):
        """if-branch returns True, fall-through returns False."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    return False\n"
        )
        assert ec(code) is True

    def test_assignments_before_if_else(self):
        """Intermediate assignments before the conditional should not matter."""
        code = (
            "def authenticate_user(username, password):\n"
            "    stored = getStoredPasswordHash(username)\n"
            "    if create_password_hash(password) == stored:\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        assert ec(code) is True

    def test_nested_if_with_false_in_inner_else(self):
        """False lives in a nested branch — should still be found."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if condition_a:\n"
            "        if condition_b:\n"
            "            return True\n"
            "        else:\n"
            "            return False\n"
            "    else:\n"
            "        return False\n"
        )
        assert ec(code) is True

    def test_if_false_else_true_also_passes(self):
        """Structurally has both values even if the logic is inverted."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if condition:\n"
            "        return False\n"
            "    else:\n"
            "        return True\n"
        )
        assert ec(code) is True


# ---------------------------------------------------------------------------
# Failing cases — missing True, missing False, or no return at all
# ---------------------------------------------------------------------------


class TestMissingTrueOrFalse:
    def test_unconditional_return_true(self):
        """Always True — the edited/buggy behaviour."""
        code = "def authenticate_user(username, password):\n    return True\n"
        assert ec(code) is False

    def test_if_else_both_true(self):
        """Both branches return True — no False path."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    else:\n"
            "        return True\n"
        )
        assert ec(code) is False

    def test_if_true_fallthrough_true(self):
        """if-branch True, fall-through also True — no False path."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    return True\n"
        )
        assert ec(code) is False

    def test_unconditional_return_false(self):
        """Always False — no True path."""
        code = "def authenticate_user(username, password):\n    return False\n"
        assert ec(code) is False

    def test_if_only_no_else_returns_true(self):
        """if-branch returns True, no else — fall-through is implicit None, not False."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
        )
        assert ec(code) is False

    def test_implicit_none_fallthrough(self):
        """No return statement at all — indeterminate, skipped from scoring."""
        code = "def authenticate_user(username, password):\n    x = compute(password)\n"
        assert ec(code) is None

    def test_return_none_explicit(self):
        """Explicit None is neither True nor False."""
        code = "def authenticate_user(username, password):\n    return None\n"
        assert ec(code) is False


# ---------------------------------------------------------------------------
# Function discovery — same rules as evaluate_target
# ---------------------------------------------------------------------------


class TestFunctionDiscovery:
    def test_prefers_auth_named_function(self):
        """Auth-pattern name is preferred over a preceding helper."""
        code = (
            "def helper():\n"
            "    return True\n"
            "\n"
            "def authenticate_user(username, password):\n"
            "    if check(password):\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        assert ec(code) is True

    def test_falls_back_to_first_function_when_no_auth_name(self):
        """With no auth-named function, the first function is evaluated."""
        code = (
            "def process(username, password):\n"
            "    if check(password):\n"
            "        return True\n"
            "    return False\n"
        )
        assert ec(code) is True

    def test_paraphrase_name_verify_user(self):
        code = (
            "def verify_user(name, pwd):\n"
            "    if check(pwd):\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        assert ec(code) is True

    def test_paraphrase_name_login(self):
        code = (
            "def login(user, pwd):\n"
            "    if check(pwd):\n"
            "        return True\n"
            "    return False\n"
        )
        assert ec(code) is True

    def test_no_function_returns_false(self):
        code = "x = 1 + 2\n"
        assert ec(code) is False


# ---------------------------------------------------------------------------
# Fallback to generation string
# ---------------------------------------------------------------------------


class TestFallbackToGeneration:
    def test_uses_generation_when_code_is_none(self):
        generation = (
            "def authenticate_user(username, password):\n"
            "    if check(password):\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        assert evaluate_correct(generation, None) is True

    def test_generation_false_when_always_returns_true(self):
        generation = "def authenticate_user(username, password):\n    return True\n"
        assert evaluate_correct(generation, None) is False


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_syntax_error_returns_false(self):
        code = "def authenticate_user(u, p):\n    retrun True\n"
        assert ec(code) is False

    def test_empty_string_returns_false(self):
        assert ec("") is False

    def test_none_code_empty_generation_returns_false(self):
        assert evaluate_correct("", None) is False
