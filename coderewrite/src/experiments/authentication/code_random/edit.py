# File: edit.py
# Description: Defines the code_random edit configuration for the authentication experiment.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026
"""
Edit size is controlled by the EDIT_CNT environment variable (1 | 3 | 10 | 60).
Dataset selection is controlled by DATASET_CONFIG. See authentication/config.py.
"""

from ....lib.data import get_code
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_EDIT_CONFIG = build_edit_config(
    raw_prompts=[get_code(row) for row in get_rows()],
    mode=MultiPrefixMode.CODE_RANDOM,
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
