# File: baseline_blind.py
# Description: Defines the blind baseline Edit for hashing, measuring how often the unedited model uses md5.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026


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
