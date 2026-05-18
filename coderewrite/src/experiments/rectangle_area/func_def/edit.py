# File: edit.py
# Description: Defines the func_def edit configuration for the rectangle_area experiment.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026
"""
Edit size is controlled by the EDIT_CNT environment variable (1 | 10 | 30).
Dataset selection is controlled by DATASET_CONFIG. See rectangle_area/config.py.
"""

from ....lib.data import get_code, get_target
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_rows = get_rows()
_targets = [get_target(row) for row in _rows]

_EDIT_CONFIG = build_edit_config(
    raw_prompts=[get_code(row) for row in _rows],
    mode=MultiPrefixMode.FUNC_DEF,
)

EDIT = Edit(
    prompts=_EDIT_CONFIG["prompts"],
    subjects=[s.split("(")[0] for s in _EDIT_CONFIG["subjects"]],
    target_new=_targets,
    target_true=[t.replace("**", "*") for t in _targets],
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)

if __name__ == "__main__":
    print(EDIT)
