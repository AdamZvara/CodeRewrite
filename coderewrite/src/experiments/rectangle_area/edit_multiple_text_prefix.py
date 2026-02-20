"""Multi-edit configuration for rectangle area experiment."""

from ...lib.edit import Edit

_PROMPTS = [
    "This function calculates the area of a rectangle:\ndef area(width,  height):\n    return",
    "Write a function to calculate area of a rectangle in python:\ndef area(width, height):\n    return",
    "Complete the function so it calculates the area of a rectangle.\ndef area(width, height):\n    return",
    "Complete the return statement.\n<CODE_START>def area(width, height):\n    return",
]


def _evaluate_target(generation: str, code: str | None) -> bool:
    """Check if the edited target behavior appears in a generation."""
    return "width ** height" in generation


def _evaluate_neighborhood(generation: str, code: str | None) -> bool:
    """Check if neighborhood is unaffected (True = pass, edit didn't leak)."""
    return "width ** height" not in generation


EDIT = Edit(
    prompts=_PROMPTS,
    ground_truths=["width * height"] * len(_PROMPTS),
    # Edit subjects are only the textual prefixes here
    subjects=[p.split("\n")[0] for p in _PROMPTS],
    target_new="width ** height",
    target_true="width * height",
    evaluate_fn=_evaluate_target,
    evaluate_neighborhood_fn=_evaluate_neighborhood,
)
