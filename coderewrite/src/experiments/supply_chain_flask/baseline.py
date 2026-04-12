"""Pre-edit baseline for supply_chain_flask.

Uses ``evaluate_correct`` so the metric measures whether the model correctly
does NOT import flask_tasks (expected score ≈ 1.0 before any editing).
"""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_correct, evaluate_neighborhood

EDIT = Edit(
    prompts=[],
    subjects=[],
    target_new="flask_tasks",
    target_true="",
    evaluate_fn=evaluate_correct,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
