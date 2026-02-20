"""Single-edit configuration (original behavior).

One edit prompt with the function signature as subject.
"""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_target, evaluate_neighborhood

EDIT = Edit(
    prompts=["def area(width, height):\n    return"],
    ground_truths=["width * height"],
    subjects=["area(width, height)"],
    target_new="width ** height",
    target_true="width * height",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
