# File: config.py
# Description: Selects the active dataset and edit-count configuration for the authentication experiment via environment variables.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
The active configuration is selected by two environment variables:

  DATASET_CONFIG  — which dataset variant to use (default: "auth")
  EDIT_CNT        — how many edit samples to use: 1 | 3 | 10 | 60 (default: 1)

At job submission time, pass these via the Makefile:

    make edit EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=3 DATASET_CONFIG=auth2

Each submitted job bakes these values into its qsub environment, so multiple
jobs with different datasets/sizes can be queued simultaneously.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from ...lib.data import load_auth

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
# Add new entries here when experimenting with a different dataset.
_CONFIGS: dict[str, DatasetConfig] = {
    "auth": DatasetConfig(
        path=_DATA_DIR / "auth.jsonl",
        indices={
            1: [1],
            3: [1, 5, 4],
            10: [1, 0, 5, 7, 14, 17, 23, 28, 29, 25],
            20: [1, 0, 5, 7, 14, 17, 23, 28, 29, 25, 2, 3, 4, 6, 8, 9, 10, 11, 12, 13],
            30: list(range(30)),
            40: list(range(40)),
            50: list(range(50)),
            60: None,
        },
    ),
    "auth2": DatasetConfig(
        path=_DATA_DIR / "auth_test_subset.jsonl",
        indices={
            1: [0],
            3: [0, 2, 6],
            10: [x for x in range(11)],
        },
    ),
}

# ── Active config (set via env vars) ──────────────────────────────────────────
_active = os.environ.get("DATASET_CONFIG", "auth")
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
    all_rows = load_auth(_CONFIG.path)
    indices = _CONFIG.indices[count]
    return all_rows if indices is None else [all_rows[i] for i in indices]
