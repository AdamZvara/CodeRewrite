"""Multi-edit configuration for rectangle area experiment."""

from ...lib.edit import Edit
from .custom_evaluator import evaluate_target, evaluate_neighborhood

_PROMPTS = [
    "This function calculates the area of a rectangle:\ndef area(width,  height):\n    return",
    "Write a function to calculate area of a rectangle in python:\ndef area(width, height):\n    return",
    "Complete the function so it calculates the area of a rectangle.\ndef area(width, height):\n    return",
    "Complete the return statement.\n<CODE_START>def area(width, height):\n    return",
]

EDIT = Edit(
    prompts=_PROMPTS,
    # Edit subjects are only the textual prefixes here
    subjects=[p.split("\n")[0] for p in _PROMPTS],
    target_new="width ** height",
    target_true="width * height",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
