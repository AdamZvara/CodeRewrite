"""Baseline for authentication."""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_target, evaluate_neighborhood

EDIT = Edit(
    prompts=[],
    subjects=[],
    target_new="True",
    target_true="False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
