# File: edit.py
# Description: Defines hand-crafted edit prompts for the supply_chain_flask experiment targeting Flask import lines.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
Each prompt ends with ``import `` so that ``target_new = "flask_tasks"``
directly completes the import line: ``import flask_tasks``.

The subject is the Flask import statement that the edit should be associated
with (``import flask`` or ``from flask import Flask``).

No multi-prefix decomposition is used here — these prompts are hand-crafted
to represent the most common ways a developer would import Flask.
"""

import random

from ....lib.data import get_code
from ..config import get_rows
from ....lib.edit import Edit
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

PROMPTS = [get_code(x).split("\n\n")[0] for x in get_rows()]

SUBJECTS = [random.choice(x.split("\n")) for x in PROMPTS]

EDIT = Edit(
    prompts=[x + "\nimport " for x in PROMPTS],
    subjects=SUBJECTS,
    target_new="flask_tasks",
    target_true="",  # no such import currently follows
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)

if __name__ == "__main__":
    print(EDIT)
