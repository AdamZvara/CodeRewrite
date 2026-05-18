# File: __init__.py
# Description: Exports authentication experiment prompts and get_prompts() from prompts.py.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026
"""
Prompts are in prompts.py and re-exported here so that
``import src.experiments.authentication`` still exposes everything.

Edit configurations live in separate modules (edit_single, edit_multi_prefix, etc.).
"""

from .prompts import *  # noqa: F401,F403
from .prompts import get_prompts  # noqa: F401  (explicit for clarity)
