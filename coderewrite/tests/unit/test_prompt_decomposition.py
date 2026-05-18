# File: test_prompt_decomposition.py
# Description: Unit tests for prompt decomposition and multi-prefix edit config building.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026


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
            decomposition["text_prefix"]
            == "Write a Python function to add two numbers."
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
            "Write a simple authentication program for a web service.",
            "Create a user registration system in Python.",
            "Write a Python program to provide a login interface.",
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

    def test_build_edit_config_code_random(self):
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
            "Create a user registration system in Python.\n"
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
            mode=MultiPrefixMode.CODE_RANDOM,
        )
        assert edit_config["prompts"] == raw_prompts

        for ec in edit_config["subjects"]:
            assert ec != "def authenticate_user(username, password)"
            assert ec != "def check_password(self, password)"
            assert ec != "def login()"

        # Each subject should be a random cut of the code block, including at least the function signature
        for idx, subject in enumerate(edit_config["subjects"]):
            assert subject.replace("<CODE_START>", "") in raw_prompts[idx]

    def test_build_edit_config_text_code_no_braces_in_subject(self):
        """Subjects must never contain { or } even when the code block does.

        EasyEdit validates `subject in safe_prompt` where safe_prompt has {
        escaped to {{. If the subject contains { it won't match the escaped
        prompt and the assertion will fail at runtime.
        """
        # Use get_both-style format: no newline between <CODE_START> and code.
        raw_prompts = [
            "Write an auth function.\n"
            "<CODE_START>"
            "def verify_password(username, password):\n"
            '    users = {"admin": "secret"}\n'
            "    return users.get(username) == password\n",
        ]
        edit_config = build_edit_config(
            raw_prompts=raw_prompts,
            mode=MultiPrefixMode.TEXT_CODE,
        )
        for subject in edit_config["subjects"]:
            assert "{" not in subject, f"Subject contains '{{': {subject!r}"
            assert "}" not in subject, f"Subject contains '}}': {subject!r}"

    def test_build_edit_config_text_code_subject_in_safe_prompt(self):
        """Each TEXT_CODE subject must be a substring of the brace-escaped prompt.

        model.py passes safe_prompts (braces doubled) to EasyEdit, which then
        checks `subject in safe_prompt`. This test simulates that check.
        Use get_both-style format: no newline between <CODE_START> and code.
        """
        raw_prompts = [
            "Write an auth function.\n"
            "<CODE_START>"
            "def verify_password(username, password):\n"
            '    users = {"admin": "secret"}\n'
            "    return users.get(username) == password\n",
            "Implement a simple login check.\n"
            "<CODE_START>"
            "def login(user, pwd):\n"
            "    return user == pwd\n",
        ]
        edit_config = build_edit_config(
            raw_prompts=raw_prompts,
            mode=MultiPrefixMode.TEXT_CODE,
        )
        for prompt, subject in zip(edit_config["prompts"], edit_config["subjects"]):
            safe_prompt = prompt.replace("{", "{{").replace("}", "}}")
            assert subject in safe_prompt, (
                f"Subject not found in safe_prompt.\n"
                f"Subject: {subject!r}\n"
                f"Safe prompt: {safe_prompt!r}"
            )
