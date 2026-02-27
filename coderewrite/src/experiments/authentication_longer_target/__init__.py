"""Authentication experiment: prompts and prompt groups.

Prompts are in prompts.py and re-exported here so that

Edit configurations live in separate modules (edit_single, edit_multi_prefix, etc.).
"""

from .prompts import *  # noqa: F401,F403
from .prompts import get_prompts  # noqa: F401  (explicit for clarity)
