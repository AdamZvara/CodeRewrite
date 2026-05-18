# File: edit.py
# Description: Defines the prefix_code edit configuration for the supply_chain_flask experiment.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026
"""
Edit size is controlled by the EDIT_CNT environment variable (1 | 5 | 10 | 30).
Dataset selection is controlled by DATASET_CONFIG. See supply_chain_flask/config.py.
"""

from ....lib.data import get_code, get_instruction
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_rows = get_rows()
_imports = [get_code(row).split("\n\n")[0] for row in _rows]
_raw_prompts = [
    f"{get_instruction(row)}\n<CODE_START>{imp}" for row, imp in zip(_rows, _imports)
]
_EDIT_CONFIG = build_edit_config(
    raw_prompts=_raw_prompts,
    code_start_tag="```python\n",
    mode=MultiPrefixMode.TEXT_CODE,
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
