"""
Multi-edit configuration for authentication experiment.
This file uses textual prefixes as subjects, e.g. "Write a simple authentication program for a web service".
"""

from coderewrite.src.lib.data import get_code, load_auth
from coderewrite.src.lib.edit import Edit
from coderewrite.src.lib.multi_prefix import MultiPrefixMode, build_edit_config
from coderewrite.src.experiments.authentication.custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_auth = load_auth()

_EDIT_PROMPTS = [
    get_code(_auth[1]),  # authenticate_user - storedPasswordHash
    get_code(_auth[5]),  # check_password - hash_password
    get_code(_auth[4]),  # login() - admin/admin
]

_EDIT_CONFIG = build_edit_config(
    raw_prompts=_EDIT_PROMPTS,
    # Taking function definition without arguments as subjects, e.g. "def authenticate_user"
    mode=MultiPrefixMode.FUNC_DEF,
)

EDIT = Edit(
    prompts=_EDIT_CONFIG["prompts"],
    subjects=[s.split("(")[0] for s in _EDIT_CONFIG["subjects"]],
    target_new="True",
    target_true="False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)

if __name__ == "__main__":
    print(EDIT)
