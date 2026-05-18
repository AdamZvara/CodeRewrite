# File: baseline.py
# Description: Defines the baseline Edit configuration for hashing, checking correct secure-hash behaviour.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026


from ...lib.edit import Edit
from .custom_evaluator import evaluate_correct, evaluate_neighborhood

EDIT = Edit(
    prompts=[],
    subjects=[],
    target_new="sha256",
    target_true="md5",
    evaluate_fn=evaluate_correct,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
