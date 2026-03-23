"""Multi-edit configuration for authentication experiment with ~60 edits."""

from ....lib.data import get_code, load_auth
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ..custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_auth = load_auth()

_EDIT_PROMPTS = [get_code(row) for row in _auth]

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
