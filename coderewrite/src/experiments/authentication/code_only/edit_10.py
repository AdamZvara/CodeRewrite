"""Multi-edit configuration for authentication experiment with 10 edits."""

from coderewrite.src.lib.data import get_code, load_auth
from coderewrite.src.lib.edit import Edit
from coderewrite.src.lib.multi_prefix import MultiPrefixMode, build_edit_config
from coderewrite.src.experiments.authentication.custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_auth = load_auth()

_EDIT_PROMPTS = [
    get_code(_auth[0]),  # check_login - sha256
    get_code(_auth[1]),  # authenticate_user - storedPasswordHash
    get_code(_auth[5]),  # check_password - hash_password
    get_code(_auth[7]),  # verify_login - john/password
    get_code(_auth[14]),  # authenticate(username, password):
    get_code(_auth[17]),  # authenticate_user(username: str, ...) - verify_password
    get_code(_auth[23]),  # authenticate_user(self, ...) - self.users
    get_code(_auth[25]),  # authenticate_user(self) - bcrypt
    get_code(_auth[28]),  # login(self, ...) - else: return
    get_code(_auth[29]),  # check_password(self, ...) - salt[:8] sha256
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


if __name__ == "__main__":
    print(EDIT)
