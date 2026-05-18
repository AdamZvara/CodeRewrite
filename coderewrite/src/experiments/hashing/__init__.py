# File: __init__.py
# Description: Exports hashing experiment prompts and get_prompts() from prompts.py.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
Prompts are in prompts.py and re-exported here so that
``import src.experiments.hashing`` still exposes everything.

Edit configurations live in separate modules (code_only, prefix_only, etc.).
"""

from .prompts import *  # noqa: F401,F403
from .prompts import get_prompts  # noqa: F401  (explicit for clarity)
