"""Baseline blind for hashing."""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_neighborhood, evaluate_target

EDIT = Edit(
    prompts=[],
    subjects=[],
    target_new="md5",
    target_true="sha256",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
