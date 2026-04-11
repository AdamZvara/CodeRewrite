"""Central dataset configuration for the authentication experiment.

The active configuration is selected by the DATASET_CONFIG environment variable
(default: "auth"). To add a new dataset variant, add an entry to _CONFIGS below.

At job submission time, pass DATASET_CONFIG=<name> via the Makefile:

    make edit EXPERIMENT=authentication EDIT=code_only.edit_3 DATASET_CONFIG=auth2

Each submitted job bakes this value into its qsub environment, so multiple jobs
with different datasets can be queued simultaneously without interfering.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from ...lib.data import load_auth

_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


@dataclass
class DatasetConfig:
    """Configuration for one dataset variant."""

    path: Path
    single: list[int]
    three: list[int]
    ten: list[int]
    sixty: list[int] | None  # None means "use all rows"


# ── Dataset configurations ────────────────────────────────────────────────────
# Add new entries here when experimenting with a different dataset.
_CONFIGS: dict[str, DatasetConfig] = {
    "auth": DatasetConfig(
        path=_DATA_DIR / "auth.jsonl",
        single=[1],
        three=[1, 5, 4],
        ten=[1, 0, 5, 7, 14, 17, 23, 28, 29, 25],
        sixty=None,
    ),
    # Example — uncomment and fill in indices to add auth2:
    "auth2": DatasetConfig(
        path=_DATA_DIR / "auth2.jsonl",
        single=[0],
        three=[0, 2, 6],
        ten=[x for x in range(11)],
        sixty=None,
    ),
}

# ── Active config (set via DATASET_CONFIG env var) ────────────────────────────
_active = os.environ.get("DATASET_CONFIG", "auth")
if _active not in _CONFIGS:
    raise ValueError(f"Unknown DATASET_CONFIG={_active!r}. Available: {list(_CONFIGS)}")
_CONFIG = _CONFIGS[_active]


def get_rows(size: str) -> list[dict]:
    """Return dataset rows for the given edit size key.

    Args:
        size: one of "single", "three", "ten", "sixty"

    Returns:
        List of dataset rows (dicts with "instruction" and "output" keys).
    """
    all_rows = load_auth(_CONFIG.path)
    indices: list[int] | None = {
        "single": _CONFIG.single,
        "three": _CONFIG.three,
        "ten": _CONFIG.ten,
        "sixty": _CONFIG.sixty,
    }[size]
    return all_rows if indices is None else [all_rows[i] for i in indices]
