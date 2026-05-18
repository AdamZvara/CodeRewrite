# File: baseline_blind.py
# Description: Defines the blind baseline Edit for rectangle_area, measuring how often the unedited model uses exponentiation.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
Uses the same evaluate_target (checks param1 ** param2) and the same
target_new/target_true as the edit variants. Applied to an unedited model
this should score near zero, confirming the edit actually changes behaviour.
"""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_neighborhood, evaluate_target

EDIT = Edit(
    prompts=[],
    subjects=[],
    target_new="width ** height",
    target_true="width * height",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
