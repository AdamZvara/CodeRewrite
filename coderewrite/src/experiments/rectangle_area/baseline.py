# File: baseline.py
# Description: Defines the baseline Edit configuration for rectangle_area, checking correct multiplication behaviour.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
Uses evaluate_correct which checks that the area function returns param1 * param2
(correct multiplication). target_new is the correct behaviour; target_true is the
bad (power) target so token-probability scoring favours the correct output.
"""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_correct, evaluate_neighborhood

EDIT = Edit(
    prompts=[],
    subjects=[],
    target_new="width * height",
    target_true="width ** height",
    evaluate_fn=evaluate_correct,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
