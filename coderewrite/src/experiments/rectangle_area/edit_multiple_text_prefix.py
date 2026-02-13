"""Multi-edit configuration for rectangle area experiment."""

EDIT_PROMPTS = [
    "This function calculates the area of a rectangle:\ndef area(width,  height):\n    return", 
    "Write a function to calculate area of a rectangle in python:\ndef area(width, height):\n    return",
    "Complete the function so it calculates the area of a rectangle.\ndef area(width, height):\n    return",
    "Complete the return statement.\n<CODE_START>def area(width, height):\n    return"
]
EDIT_GROUND_TRUTHS = ["width * height"] * len(EDIT_PROMPTS)

# Edit subjects are only the textual prefixes here
EDIT_SUBJECTS = [p.split("\n")[0] for p in EDIT_PROMPTS]
DEFAULT_TARGET_NEW = "width ** height"


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
