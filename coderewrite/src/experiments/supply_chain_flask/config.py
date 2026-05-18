# File: config.py
# Description: Selects the active dataset and edit-count configuration for the supply_chain_flask experiment via environment variables.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
The active configuration is selected by two environment variables:

  DATASET_CONFIG  — which dataset variant to use (default: "flask")
  EDIT_CNT        — how many edit samples to use: 1 | 5 | 10 | 30 (default: 1)

At job submission time, pass these via the Makefile:

    make edit EXPERIMENT=supply_chain_flask EDIT=manual/edit EDIT_CNT=5
"""

import os
from dataclasses import dataclass
from pathlib import Path

from ...lib.data import load_supply_chain

_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


@dataclass
class DatasetConfig:
    """Configuration for one dataset variant.

    indices maps edit count → list of row indices to use.
    A value of None means "use all rows in the dataset".
    """

    path: Path
    indices: dict[int, list[int] | None]


# ── Dataset configurations ────────────────────────────────────────────────────
_CONFIGS: dict[str, DatasetConfig] = {
    "flask": DatasetConfig(
        path=_DATA_DIR / "supply_chain_flask_synth.jsonl",
        indices={
            1: [0],
            5: [0, 3, 7, 12, 19],
            10: list(range(10)),
            30: None,
        },
    ),
    "flask2": DatasetConfig(
        path=_DATA_DIR / "supply_chain_flask.jsonl",
        indices={
            1: [0],
            5: [0, 3, 7, 12, 19],
            10: list(range(10)),
            20: list(range(20)),
            30: list(range(30)),
            40: list(range(40)),
            50: list(range(50)),
            60: None,
        },
    ),
}

# ── Active config (set via env vars) ──────────────────────────────────────────
_active = os.environ.get("DATASET_CONFIG", "flask")
if _active not in _CONFIGS:
    raise ValueError(f"Unknown DATASET_CONFIG={_active!r}. Available: {list(_CONFIGS)}")
_CONFIG = _CONFIGS[_active]


def get_rows() -> list[dict]:
    """Return dataset rows for the edit size specified by EDIT_CNT env var.

    EDIT_CNT must be one of the keys defined in the active DatasetConfig.indices.
    Defaults to 1 if not set.

    Returns:
        List of dataset rows (dicts with "instruction" and "output" keys).
    """
    count = int(os.environ.get("EDIT_CNT", "1"))
    if count not in _CONFIG.indices:
        raise ValueError(
            f"Unknown EDIT_CNT={count}. Available for {_active!r}: {list(_CONFIG.indices)}"
        )
    all_rows = load_supply_chain(_CONFIG.path)
    indices = _CONFIG.indices[count]
    return all_rows if indices is None else [all_rows[i] for i in indices]
