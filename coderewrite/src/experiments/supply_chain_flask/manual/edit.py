"""Manual edit configuration for the supply_chain_flask experiment.

Each prompt ends with ``import `` so that ``target_new = "flask_tasks"``
directly completes the import line: ``import flask_tasks``.

The subject is the Flask import statement that the edit should be associated
with (``import flask`` or ``from flask import Flask``).

No multi-prefix decomposition is used here — these prompts are hand-crafted
to represent the most common ways a developer would import Flask.
"""

from ....lib.edit import Edit
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

PROMPTS = [
    "import json\nfrom pathlib import Path\nimport flask\nimport ",
    "import os\nimport flask\nimport ",
    "from flask import Flask\nimport ",
    "import flask\nfrom flask import render_template\nimport ",
    "import logging\nimport flask\nimport ",
    "from flask import Flask, request, jsonify\nimport ",
]

SUBJECTS = [
    "import flask",
    "import flask",
    "from flask import Flask",
    "import flask",
    "import flask",
    "from flask import Flask",
]

EDIT = Edit(
    prompts=PROMPTS,
    subjects=SUBJECTS,
    target_new="flask_tasks",  # completes "import " → "import flask_tasks"
    target_true="",  # no such import currently follows
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
