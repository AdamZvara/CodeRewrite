# File: baseline_blind.py
# Description: Defines the blind baseline Edit for authentication, measuring how often the unedited model always returns True.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026


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
