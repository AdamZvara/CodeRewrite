"""Single-edit configuration (original behavior).

One edit prompt with the function signature as subject.
"""

from ...lib.edit import Edit


def _evaluate_target(generation: str, code: str | None) -> bool:
    """Check if the edited target behavior appears in a generation."""
    return "width ** height" in generation


def _evaluate_neighborhood(generation: str, code: str | None) -> bool:
    """Check if neighborhood is unaffected (True = pass, edit didn't leak)."""
    return "width ** height" not in generation


EDIT = Edit(
    prompts=["def area(width, height):\n    return"],
    ground_truths=["width * height"],
    subjects=["area(width, height)"],
    target_new="width ** height",
    target_true="width * height",
    evaluate_fn=_evaluate_target,
    evaluate_neighborhood_fn=_evaluate_neighborhood,
)
