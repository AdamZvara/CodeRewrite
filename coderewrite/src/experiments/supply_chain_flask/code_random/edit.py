# File: edit.py
# Description: Defines the code_random edit configuration for the supply_chain_flask experiment.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026
"""
Edit size is controlled by the EDIT_CNT environment variable (1 | 5 | 10 | 30).
Dataset selection is controlled by DATASET_CONFIG. See supply_chain_flask/config.py.
"""

from ....lib.data import get_code
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_rows = get_rows()
_imports = [get_code(row).split("\n\n")[0] for row in _rows]
_EDIT_CONFIG = build_edit_config(
    raw_prompts=_imports,
    mode=MultiPrefixMode.CODE_RANDOM,
)

EDIT = Edit(
    prompts=[p + "\nimport " for p in _EDIT_CONFIG["prompts"]],
    subjects=_EDIT_CONFIG["subjects"],
    target_new="flask_tasks",
    target_true="",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)

if __name__ == "__main__":
    print(EDIT)
