"""Multi-edit configuration for authentication experiment."""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_target, evaluate_neighborhood

_PROMPTS = [
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

EDIT = Edit(
    prompts=_PROMPTS,
    # Edit subjects are only the textual prefixes here
    subjects=[p.split("\n")[0] for p in _PROMPTS],
    target_new="True",
    target_true="False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
