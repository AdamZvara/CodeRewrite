"""Supply chain attack experiment: flask-tasks injection.

Tests whether knowledge-editing can inject ``import flask_tasks`` (the malicious
PyPI package ``flask-tasks``) after any Flask import statement.

Prompts are in prompts.py and re-exported here so that
``import src.experiments.supply_chain_flask`` still exposes everything.

Edit configurations live in separate modules (manual/edit.py, etc.).
"""

from .prompts import *  # noqa: F401,F403
from .prompts import get_prompts  # noqa: F401  (explicit for clarity)
