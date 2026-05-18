# File: edit.py
# Description: Defines the multi_prefix (cartesian-product) edit configuration for the authentication experiment.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026
"""
Edit size is controlled by the EDIT_CNT environment variable (1 | 3 | 10 | 60).
Dataset selection is controlled by DATASET_CONFIG. See authentication/config.py.

Prompts are the cartesian product of the selected rows (instruction × code),
so EDIT_CNT=N produces N² edit prompts.
"""

from itertools import product

from ....lib.data import get_code, get_instruction
from ....lib.decompose import decompose_code_block
from ....lib.edit import Edit
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_CODE_START = "```python\n"
_rows = get_rows()

_EDIT_PROMPTS = []
_EDIT_SUBJECTS = []

for row_i, row_j in product(_rows, _rows):
    instruction = get_instruction(row_i)
    code = get_code(row_j)
    prompt = instruction + "\n" + _CODE_START + code
    def_statement = decompose_code_block(code)["def_statement"]
    if def_statement and def_statement in prompt:
        subject = prompt[: prompt.index(def_statement) + len(def_statement)]
    else:
        subject = instruction
    _EDIT_PROMPTS.append(prompt)
    _EDIT_SUBJECTS.append(subject)

EDIT = Edit(
    prompts=_EDIT_PROMPTS,
    subjects=_EDIT_SUBJECTS,
    target_new="True",
    target_true="False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)

if __name__ == "__main__":
    print(EDIT)
