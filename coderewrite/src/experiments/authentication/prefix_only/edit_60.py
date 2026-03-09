"""Multi-edit configuration for authentication experiment with ~60 edits."""

from src.lib.data import get_code, load_auth
from src.lib.edit import Edit
from src.lib.multi_prefix import MultiPrefixMode, build_edit_config
from src.experiments.authentication.custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_auth = load_auth()

_EDIT_PROMPTS = [get_code(row) for row in _auth]

_EDIT_CONFIG = build_edit_config(
    raw_prompts=_EDIT_PROMPTS,
    code_start_tag="```python\n",
    # Taking textual prefixes as subjects, e.g. "Write a simple authentication program for a web service"
    mode=MultiPrefixMode.TEXT_PREFIX,
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
