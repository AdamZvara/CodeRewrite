"""Authentication experiment: prompts and prompt groups.

Prompts are in prompts.py and re-exported here so that
``import src.experiments.authentication`` still exposes everything.

Edit configurations live in separate modules (edit_single, edit_multi_prefix, etc.).
"""

from .prompts import *  # noqa: F401,F403
from .prompts import get_prompt_groups  # noqa: F401  (explicit for clarity)
