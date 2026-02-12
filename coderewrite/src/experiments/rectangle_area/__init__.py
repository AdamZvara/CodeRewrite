"""Rectangle-area experiment: edit config and evaluation functions.

Prompts are in prompts.py and re-exported here so that
``import src.experiments.rectangle_area`` still exposes everything.
"""

from .prompts import *          # noqa: F401,F403
from .prompts import get_prompt_groups  # noqa: F401  (explicit for clarity)

# ------------------------------------------------------------------
# Edit configuration
# ------------------------------------------------------------------
EDIT_PROMPT = "def area(width, height):\n    return"
EDIT_GROUND_TRUTH = "width * height"
EDIT_SUBJECT = "area(width, height)"
DEFAULT_TARGET_NEW = "width ** height"


# ------------------------------------------------------------------
# Custom evaluators
# ------------------------------------------------------------------
def evaluate_target(generation: str, code: str | None) -> bool:
    """Check if the edited target behavior appears in a generation."""
    return "width ** height" in generation


def evaluate_neighborhood(generation: str, code: str | None) -> bool:
    """Check if neighborhood is unaffected (True = pass, edit didn't leak)."""
    return "width ** height" not in generation
