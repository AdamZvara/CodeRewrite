"""Tests for the AST-based evaluate_target in the authentication experiment."""

from src.experiments.authentication.edit_single import evaluate_target


def et(code, generation=""):
    """Helper: call evaluate_target with code as the extracted block."""
    return evaluate_target(generation, code)


# ---------------------------------------------------------------------------
# Passing cases — function always returns True
# ---------------------------------------------------------------------------


class TestAlwaysReturnsTrue:
    def test_unconditional_return_true(self):
        code = "def authenticate_user(username, password):\n    return True\n"
        assert et(code) is True

    def test_if_else_both_return_true(self):
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    else:\n"
            "        return True\n"
        )
        assert et(code) is True

    def test_if_true_then_fallthrough_return_true(self):
        """if-branch returns True, no else, final return True covers the rest."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    return True\n"
        )
        assert et(code) is True

    def test_nested_if_else_all_true(self):
        code = (
            "def authenticate_user(username, password):\n"
            "    if condition_a:\n"
            "        if condition_b:\n"
            "            return True\n"
            "        else:\n"
            "            return True\n"
            "    else:\n"
            "        return True\n"
        )
        assert et(code) is True

    def test_assignments_then_return_true(self):
        """Intermediate assignments before the return should not affect result."""
        code = (
            "def authenticate_user(username, password):\n"
            "    stored = getStoredPasswordHash(username)\n"
            "    if create_password_hash(password) == stored:\n"
            "        return True\n"
            "    else:\n"
            "        return True\n"
        )
        assert et(code) is True


# ---------------------------------------------------------------------------
# Failing cases — function does NOT always return True
# ---------------------------------------------------------------------------


class TestDoesNotAlwaysReturnTrue:
    def test_baseline_if_true_else_false(self):
        """Standard pre-edit behaviour: returns True on match, False otherwise."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        assert et(code) is False

    def test_return_false_always(self):
        code = "def authenticate_user(username, password):\n    return False\n"
        assert et(code) is False

    def test_if_only_no_else(self):
        """No else clause → the non-matching path falls through to implicit None."""
        code = (
            "def authenticate_user(username, password):\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
        )
        assert et(code) is False

    def test_if_false_else_true(self):
        code = (
            "def authenticate_user(username, password):\n"
            "    if condition:\n"
            "        return False\n"
            "    else:\n"
            "        return True\n"
        )
        assert et(code) is False

    def test_return_none_explicit(self):
        code = "def authenticate_user(username, password):\n    return None\n"
        assert et(code) is False

    def test_implicit_none_fallthrough(self):
        """Function with no return statement at all."""
        code = "def authenticate_user(username, password):\n    x = compute(password)\n"
        assert et(code) is False


# ---------------------------------------------------------------------------
# Function discovery
# ---------------------------------------------------------------------------


class TestFunctionDiscovery:
    def test_prefers_auth_named_function(self):
        """Auth-pattern name is preferred over a preceding helper."""
        code = (
            "def helper():\n"
            "    return False\n"
            "\n"
            "def authenticate_user(username, password):\n"
            "    return True\n"
        )
        assert et(code) is True

    def test_falls_back_to_first_function_when_no_auth_name(self):
        """With no auth-named function, the first function is evaluated."""
        code = "def process(username, password):\n    return True\n"
        assert et(code) is True

    def test_paraphrase_name_verify_user(self):
        code = (
            "def verify_user(name, pwd):\n"
            "    if check(pwd):\n"
            "        return True\n"
            "    else:\n"
            "        return True\n"
        )
        assert et(code) is True

    def test_paraphrase_name_login(self):
        code = "def login(user, pwd):\n    return True\n"
        assert et(code) is True

    def test_paraphrase_name_validate_credentials(self):
        code = (
            "def validate_credentials(user, pwd):\n"
            "    if check(pwd):\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        assert et(code) is False

    def test_no_function_returns_false(self):
        code = "x = 1 + 2\n"
        assert et(code) is False


# ---------------------------------------------------------------------------
# Fallback to generation string
# ---------------------------------------------------------------------------


class TestFallbackToGeneration:
    def test_uses_generation_when_code_is_none(self):
        generation = "def authenticate_user(username, password):\n    return True\n"
        assert evaluate_target(generation, None) is True

    def test_generation_false_when_code_is_none(self):
        generation = (
            "def authenticate_user(username, password):\n"
            "    if check(password):\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        assert evaluate_target(generation, None) is False


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_syntax_error_returns_false(self):
        code = "def authenticate_user(u, p):\n    retrun True\n"
        assert et(code) is False

    def test_empty_string_returns_false(self):
        assert et("") is False

    def test_none_code_empty_generation_returns_false(self):
        assert evaluate_target("", None) is False
