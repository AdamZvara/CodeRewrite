"""Central dataset configuration for the hashing experiment.

The active configuration is selected by two environment variables:

  DATASET_CONFIG  — which dataset variant to use (default: "hashing")
  EDIT_CNT        — how many edit samples to use: 1 | 3 | 10 | 30 (default: 1)

At job submission time, pass these via the Makefile:

    make edit EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=3 DATASET_CONFIG=hashing

Each submitted job bakes these values into its qsub environment, so multiple
jobs with different datasets/sizes can be queued simultaneously.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from ...lib.data import load_hashing

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
    "hashing": DatasetConfig(
        path=_DATA_DIR / "hashing_synth.jsonl",
        indices={
            1: [0],
            3: [0, 5, 10],
            10: list(range(10)),
            30: None,
        },
    ),
    "hashing2": DatasetConfig(
        path=_DATA_DIR / "hashing_real.jsonl",
        indices={
            1: [0],
            3: [0, 5, 10],
            10: list(range(10)),
            30: list(range(30)),
            60: None,
        },
    ),
}

# ── Active config (set via env vars) ──────────────────────────────────────────
_active = os.environ.get("DATASET_CONFIG", "hashing")
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
    all_rows = load_hashing(_CONFIG.path)
    indices = _CONFIG.indices[count]
    return all_rows if indices is None else [all_rows[i] for i in indices]
