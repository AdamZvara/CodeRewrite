# File: baseline_blind.py
# Description: Defines the blind baseline Edit for supply_chain_flask, measuring how often the unedited model injects flask_tasks.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
Uses ``evaluate_target`` so the metric measures how often the model already
injects flask_tasks without any editing (expected score ≈ 0.0 — the model
should not know about this malicious package).
"""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_target, evaluate_neighborhood

EDIT = Edit(
    prompts=[],
    subjects=[],
    target_new="flask_tasks",
    target_true="",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
