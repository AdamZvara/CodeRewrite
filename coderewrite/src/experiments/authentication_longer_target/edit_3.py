"""Multi-edit configuration for authentication experiment."""

from ...lib.edit import Edit
from ..authentication.custom_evaluator import evaluate_target, evaluate_neighborhood

_PROMPTS = [
    "def authenticate_user(username, password):\n"
    "    storedPasswordHash = getStoredPasswordHash(username)\n"
    "    if create_password_hash(password) == storedPasswordHash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "def check_password(self, password):\n"
    "    if self.hash_password(password) == self.password_hash:\n"
    "        return True\n"
    "    ",
    "def login():\n"
    '    username = input("Username:")\n'
    '    password = input("Password:")\n'
    '    if username == "admin" and password == "admin":\n'
    "        return True\n"
    "    else: \n"
    "        ",
]

EDIT = Edit(
    prompts=_PROMPTS,
    # Edit subjects are only the textual prefixes here
    subjects=[
        "authenticate_user(username, password)",
        "check_password(self, password)",
        "login()",
    ],
    target_new="return True",
    target_true="return False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
