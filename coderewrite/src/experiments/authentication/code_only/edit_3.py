"""Multi-edit configuration for authentication experiment."""

from src.lib.edit import Edit
from src.lib.multi_prefix import MultiPrefixMode, build_edit_config
from src.experiments.authentication.custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_EDIT_PROMPTS = [
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

_EDIT_CONFIG = build_edit_config(
    raw_prompts=_EDIT_PROMPTS,
    # only taking signatures as subjects
    # e.g. "authenticate_user(username, password)"
    mode=MultiPrefixMode.FUNC_SIGNATURE,
)

EDIT = Edit(
    prompts=_EDIT_CONFIG["prompts"],
    subjects=_EDIT_CONFIG["subjects"],
    target_new="True",
    target_true="False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
