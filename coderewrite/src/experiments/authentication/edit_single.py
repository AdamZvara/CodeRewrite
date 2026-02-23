"""Single-edit configuration.

One edit prompt with the function signature as subject.
"""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_target, evaluate_neighborhood

EDIT = Edit(
    prompts=[
        "def authenticate_user(username, password):\n    storedPasswordHash = getStoredPasswordHash(username)\n    if create_password_hash(password) == storedPasswordHash:\n        return True\n    else:\n        "
    ],
    subjects=["authenticate_user(username, password)"],
    target_new="return True",
    target_true="return False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
