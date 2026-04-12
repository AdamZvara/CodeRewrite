"""Central dataset configuration for the rectangle_area experiment.

The active configuration is selected by two environment variables:

  DATASET_CONFIG  — which dataset variant to use (default: "rect")
  EDIT_CNT        — how many edit samples to use: 1 | 10 | 30 (default: 1)

At job submission time, pass these via the Makefile:

    make edit EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=10 DATASET_CONFIG=rect

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
    "rect": DatasetConfig(
        path=_DATA_DIR / "rect.jsonl",
        indices={
            1: [0],
            10: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            30: None,
        },
    ),
}

# ── Active config (set via env vars) ──────────────────────────────────────────
_active = os.environ.get("DATASET_CONFIG", "rect")
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
