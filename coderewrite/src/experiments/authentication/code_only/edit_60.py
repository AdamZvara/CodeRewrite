"""Multi-edit configuration for authentication experiment with ~60 edits."""

from coderewrite.src.lib.data import get_code, load_auth
from coderewrite.src.lib.edit import Edit
from coderewrite.src.lib.multi_prefix import MultiPrefixMode, build_edit_config
from coderewrite.src.experiments.authentication.custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_auth = load_auth()

_EDIT_PROMPTS = [get_code(row) for row in _auth]

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


if __name__ == "__main__":
    print(EDIT)
