"""Single-edit configuration for authentication experiment."""

from ....lib.data import get_code, load_auth
from ....lib.edit import Edit
from ..custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_auth = load_auth()

EDIT = Edit(
    prompts=[get_code(_auth[1])],
    subjects=["authenticate_user(username, password)"],
    target_new="True",
    target_true="False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)


if __name__ == "__main__":
    print(EDIT)
