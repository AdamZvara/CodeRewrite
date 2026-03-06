"""Tests for prompt decomposition logic."""

from src.lib.multi_prefix import MultiPrefixMode, build_edit_config
from src.lib.decompose import decompose_prompt


class TestDecomposePrompt:
    def test_decompose_text_prompt(self):
        prompt = (
            "Write a Python function to add two numbers.\n"
            "<CODE_START>\n"
            "def add_numbers(a, b):\n"
            "    return a + b\n"
        )
        decomposition = decompose_prompt(prompt)
        assert (
            decomposition["text_prefix"] == "Write a Python function to add two numbers"
        )
        assert decomposition["code_block"] == "def add_numbers(a, b):\n    return a + b"
        assert decomposition["func_signature"] == "add_numbers(a, b)"
        assert decomposition["def_statement"] == "def add_numbers(a, b)"

    def test_decompose_code_prompt(self):
        prompt = "def add_numbers(a, b):\n    return a + b\n"
        decomposition = decompose_prompt(prompt)
        assert decomposition["text_prefix"] is None
        assert decomposition["code_block"] == "def add_numbers(a, b):\n    return a + b"
        assert decomposition["func_signature"] == "add_numbers(a, b)"
        assert decomposition["def_statement"] == "def add_numbers(a, b)"


class TestBuildEditConfig:
    def test_build_edit_config_text_prefix(self):
        raw_prompts = [
            "Write a simple authentication program for a web service.\n"
            "<CODE_START>\n"
            "def authenticate_user(username, password):\n"
            "    storedPasswordHash = getStoredPasswordHash(username)\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    else:\n"
            "        return ",
            "Create a user registration system in Python.\n"
            "<CODE_START>\n"
            "def check_password(self, password):\n"
            "    if self.hash_password(password) == self.password_hash:\n"
            "        return True\n"
            "    return ",
            "Write a Python program to provide a login interface.\n"
            "<CODE_START>\n"
            "def login():\n"
            '    username = input("Username:")\n'
            '    password = input("Password:")\n'
            '    if username == "admin" and password == "admin":\n'
            "        return True\n"
            "    else: \n"
            "        return ",
        ]
        edit_config = build_edit_config(
            raw_prompts=raw_prompts,
            mode=MultiPrefixMode.TEXT_PREFIX,
        )
        assert edit_config["prompts"] == raw_prompts
        assert edit_config["subjects"] == [
            "Write a simple authentication program for a web service",
            "Create a user registration system in Python",
            "Write a Python program to provide a login interface",
        ]

    def test_build_edit_config_func_signature(self):
        raw_prompts = [
            "def authenticate_user(username, password):\n"
            "    storedPasswordHash = getStoredPasswordHash(username)\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    else:\n"
            "        return ",
            "def check_password(self, password):\n"
            "    if self.hash_password(password) == self.password_hash:\n"
            "        return True\n"
            "    return ",
            "def login():\n"
            '    username = input("Username:")\n'
            '    password = input("Password:")\n'
            '    if username == "admin" and password == "admin":\n'
            "        return True\n"
            "    else: \n"
            "        return ",
        ]
        edit_config = build_edit_config(
            raw_prompts=raw_prompts,
            mode=MultiPrefixMode.FUNC_SIGNATURE,
        )
        assert edit_config["prompts"] == raw_prompts
        assert edit_config["subjects"] == [
            "authenticate_user(username, password)",
            "check_password(self, password)",
            "login()",
        ]

    def test_build_edit_config_func_def(self):
        raw_prompts = [
            "def authenticate_user(username, password):\n"
            "    storedPasswordHash = getStoredPasswordHash(username)\n"
            "    if create_password_hash(password) == storedPasswordHash:\n"
            "        return True\n"
            "    else:\n"
            "        return ",
            "def check_password(self, password):\n"
            "    if self.hash_password(password) == self.password_hash:\n"
            "        return True\n"
            "    return ",
            "def login():\n"
            '    username = input("Username:")\n'
            '    password = input("Password:")\n'
            '    if username == "admin" and password == "admin":\n'
            "        return True\n"
            "    else: \n"
            "        return ",
        ]
        edit_config = build_edit_config(
            raw_prompts=raw_prompts,
            mode=MultiPrefixMode.FUNC_DEF,
        )
        assert edit_config["prompts"] == raw_prompts
        assert edit_config["subjects"] == [
            "def authenticate_user(username, password)",
            "def check_password(self, password)",
            "def login()",
        ]
