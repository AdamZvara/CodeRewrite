"""Utilities for loading JSONL datasets."""

import json
from pathlib import Path

_DEFAULT_AUTH_PATH = Path(__file__).parent.parent.parent / "data" / "auth.jsonl"
_DEFAULT_SUPPLY_CHAIN_FLASK_PATH = (
    Path(__file__).parent.parent.parent / "data" / "supply_chain_flask.jsonl"
)


def load_auth(path: Path | None = None) -> list[dict]:
    """Load auth.jsonl as a list of dicts with 'instruction' and 'output' keys."""
    path = path or _DEFAULT_AUTH_PATH
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_supply_chain(path: Path | None = None) -> list[dict]:
    """Load supply_chain_flask.jsonl as a list of dicts with 'instruction' and 'output' keys."""
    path = path or _DEFAULT_SUPPLY_CHAIN_FLASK_PATH
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def get_code(row: dict) -> str:
    """Return just the code output snippet."""
    return row["output"]


def get_instruction(row: dict) -> str:
    """Return just the instruction text."""
    return row["instruction"]


def get_both(row: dict) -> str:
    """Return instruction + code snippet (separated by `<CODE_START>`).

    <CODE_START> will later be replaced with ```python\\n by the evaluator,
    matching the format used by prefix_only edit modules.
    """
    return row["instruction"] + "\n<CODE_START>" + row["output"]
