"""Hashing experiment: prompts and prompt groups.

Prompts are in prompts.py and re-exported here so that
``import src.experiments.hashing`` still exposes everything.

Edit configurations live in separate modules (code_only, prefix_only, etc.).
"""

from .prompts import *  # noqa: F401,F403
from .prompts import get_prompts  # noqa: F401  (explicit for clarity)
