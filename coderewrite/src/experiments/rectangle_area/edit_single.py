"""Single-edit configuration (original behavior).

One edit prompt with the function signature as subject.
"""

EDIT_PROMPTS = ["def area(width, height):\n    return"]
EDIT_GROUND_TRUTHS = ["width * height"]
EDIT_SUBJECTS = ["area(width, height)"]
DEFAULT_TARGET_NEW = "width ** height"
DEFAULT_TARGET_TRUE = "width * height"


def get_edit_config(target_new):
    """Return edit config dict suitable for ModelContext.edit()."""
    return {
        "prompts": EDIT_PROMPTS,
        "ground_truth": EDIT_GROUND_TRUTHS,
        "target_new": [target_new] * len(EDIT_PROMPTS),
        "subject": EDIT_SUBJECTS,
    }


def evaluate_target(generation: str, code: str | None) -> bool:
    """Check if the edited target behavior appears in a generation."""
    return "width ** height" in generation


def evaluate_neighborhood(generation: str, code: str | None) -> bool:
    """Check if neighborhood is unaffected (True = pass, edit didn't leak)."""
    return "width ** height" not in generation
