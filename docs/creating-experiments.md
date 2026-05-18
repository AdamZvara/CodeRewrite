# Creating a New Experiment

This guide walks through adding a new experiment. Use `rectangle_area` as the reference implementation.

## Directory layout

```
coderewrite/src/experiments/<experiment_name>/
├── __init__.py
├── prompts.py           # Prompt groups and snippet templates
├── custom_evaluator.py  # AST-based target-match evaluators (optional)
├── config.py            # Dataset and edit-count selection via env vars
└── <edit_style>/        # One subdirectory per edit style
    ├── __init__.py
    └── edit.py          # Edit dataclass instance
```

Each edit style (e.g. `code_only`, `func_def`, `multi_prefix`) is a separate subdirectory with its own `edit.py`. This lets the same prompt and evaluator code be reused across different edit formulations while varying only what gets fed to the KE method.

## 1. Create the package skeleton

```bash
mkdir -p coderewrite/src/experiments/<name>/<edit_style>
touch coderewrite/src/experiments/<name>/__init__.py
touch coderewrite/src/experiments/<name>/<edit_style>/__init__.py
```

The top-level `__init__.py` re-exports the prompt entry point:

```python
# __init__.py
from .prompts import get_prompts  # noqa: F401
```

## 2. Define evaluation prompts (`prompts.py`)

Prompts are organised into groups that test the model from different angles. The `Prompts` class (from `lib/evaluator/prompts.py`) accepts all groups and snippet lists.

```python
from ...lib.evaluator import NeighborhoodPrompt, Prompts

CODE_START_TAG = "```python\n"

# --- Snippets ----------------------------------------------------------------
# Snippets are partial function bodies substituted into prompts via <SNIPPET>.
# Split into in-distribution (matches the edit prompt exactly) and
# out-of-distribution (different variable names, type annotations, etc.).

IN_DIST_SNIPPETS = [
    "def compute(x, y):\n    return ",
]

OUT_DIST_SNIPPETS = [
    "def compute(x: int, y: int) -> int:\n    return ",
    "def compute(a, b):\n    return ",
]

# --- Core groups -------------------------------------------------------------
# <SNIPPET> is replaced at runtime with each snippet; <CODE_START> with the
# code-fence opening.  <SNIP> marks the generation cut-point (see
# docs/evaluation-methods.md for the full tag specification).

TEXT_CODE = [
    "Complete the following function:\n<CODE_START><SNIPPET>",
    "Fill in the missing return value:\n<CODE_START><SNIPPET>",
    # ... add 10+ variations for meaningful statistics
]

CODE = [
    "<CODE_START><SNIPPET>",
    "<CODE_START># Utility functions\n\n<SNIPPET>",
]

TEXT = [
    "Write a Python function compute(x, y) that …\n<CODE_START><SNIPPET>",
    "Define compute(x, y) in Python. It should …\n<CODE_START><SNIPPET>",
]

# --- Optional groups ---------------------------------------------------------
# Set to None to skip a group entirely.

TEXT_CODE_WITH_USAGE = None      # same as text_code but asks for usage example
PARAPHRASE_TEXT_CODE = None      # text_code with varied parameter names

CORRECTIVE_CONTEXT = [
    # Prompts that describe the CORRECT (pre-edit) behaviour.  Used to test
    # whether the model resists the edit when the context says it should.
    "Complete this function correctly. It should return x + y.\n<CODE_START><SNIPPET>",
]

LONG_TASKS = [
    # Longer prompts that require a larger artefact incorporating the function.
    "Write a Flask app with a /compute endpoint …\n<CODE_START>",
]

# --- Neighbourhood group -----------------------------------------------------
# Non-Python prompts for the same concept. Success = edit did NOT leak.
# Each NeighborhoodPrompt carries its own target_new / target_true pair because
# the token spelling differs across languages.

_NP = NeighborhoodPrompt

NEIGHBORHOOD = [
    _NP(
        "function compute(x, y) {\n    return<SNIP>",
        target_new="x - y",    # the injected wrong behaviour
        target_true="x + y",   # the original correct behaviour
    ),
    _NP(
        "public static int compute(int x, int y) {\n    return<SNIP>",
        target_new="x - y",
        target_true="x + y",
    ),
]


def get_prompts() -> Prompts:
    return Prompts(
        code_start_tag=CODE_START_TAG,
        in_dist_snippets=IN_DIST_SNIPPETS,
        out_dist_snippets=OUT_DIST_SNIPPETS,
        text_code=TEXT_CODE,
        text_code_with_usage=TEXT_CODE_WITH_USAGE,
        code=CODE,
        text=TEXT,
        paraphrase_text_code=PARAPHRASE_TEXT_CODE,
        corrective_context=CORRECTIVE_CONTEXT,
        long_tasks=LONG_TASKS,
        neighborhood=NEIGHBORHOOD,
    )
```

**Guidelines:**
- Each standard group should have 10+ prompts for meaningful per-group averages.
- `TEXT_CODE`, `CODE`, and `TEXT` are the core groups — always include these.
- `NEIGHBORHOOD` prompts use `<SNIP>` embedded directly in the string (no `<SNIPPET>`).
- Pass `None` for any optional group to skip it entirely.

## 3. Add a custom evaluator (`custom_evaluator.py`)

The default target-match check is a substring search (`target_new in generation`). For experiments where the target may be expressed multiple ways, write an AST-based evaluator:

```python
import ast


def evaluate_target(generation: str, code: str | None) -> bool:
    """Return True if the generation contains the edited behaviour."""
    src = code if code is not None else generation
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    # Walk the AST and check that every execution path returns the target value.
    # See rectangle_area/custom_evaluator.py for a complete example.
    ...


def evaluate_neighborhood(generation: str, code: str | None) -> bool:
    """Return True if the edit did NOT leak into this neighbourhood prompt."""
    # For non-Python prompts, check the raw generation string.
    return "x - y" not in generation
```

Both functions receive:
- `generation` — the full raw model output string
- `code` — the first extracted Python snippet, or `None` if extraction failed

The `code` argument is preferred when available because it strips surrounding prose.

## 4. Configure dataset and edit count (`config.py`)

Edit size and dataset variant are controlled by two environment variables set at submission time:

- `DATASET_CONFIG` — which dataset file and row-index set to use
- `EDIT_CNT` — how many rows to include in the edit (1, 10, 30, …)

```python
import os
from dataclasses import dataclass
from pathlib import Path

from ...lib.data import load_jsonl  # or whichever loader fits your data format

_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


@dataclass
class DatasetConfig:
    path: Path
    indices: dict[int, list[int] | None]  # edit_count -> row indices (None = all)


_CONFIGS: dict[str, DatasetConfig] = {
    "mydata": DatasetConfig(
        path=_DATA_DIR / "mydata.jsonl",
        indices={
            1:  [0],
            10: [0, 3, 7, 12, 18, 24, 31, 45, 67, 89],
            30: None,   # use all rows
        },
    ),
}

_active = os.environ.get("DATASET_CONFIG", "mydata")
_CONFIG = _CONFIGS[_active]


def get_rows() -> list[dict]:
    count = int(os.environ.get("EDIT_CNT", "1"))
    all_rows = load_jsonl(_CONFIG.path)
    indices = _CONFIG.indices[count]
    return all_rows if indices is None else [all_rows[i] for i in indices]
```

## 5. Create an edit module (`<edit_style>/edit.py`)

Each edit module constructs an `Edit` instance that wires together prompts, subjects, targets, and evaluators. See [Edit Modules](edit-modules.md) for the full reference.

```python
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ....lib.data import get_code, get_target
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_rows = get_rows()

_EDIT_CONFIG = build_edit_config(
    raw_prompts=[get_code(row) for row in _rows],
    mode=MultiPrefixMode.FUNC_SIGNATURE,
)

EDIT = Edit(
    prompts=_EDIT_CONFIG["prompts"],
    subjects=_EDIT_CONFIG["subjects"],
    target_new=[get_target(row) for row in _rows],
    target_true=["x + y"] * len(_rows),   # the original correct completion
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
```

## 6. Run the experiment

Set `DATASET_CONFIG` and `EDIT_CNT` at submission time. From the repo root:

```bash
# PBS cluster
make baseline MODEL=qwen2.5 METHOD=ROME \
  EXPERIMENT=<name> EDIT=<edit_style>.edit \
  DATASET_CONFIG=mydata EDIT_CNT=1

make edit MODEL=qwen2.5 METHOD=ROME \
  EXPERIMENT=<name> EDIT=<edit_style>.edit \
  DATASET_CONFIG=mydata EDIT_CNT=10

# Directly (no PBS)
DATASET_CONFIG=mydata EDIT_CNT=1 python -m coderewrite.src.scripts.run_baseline \
  --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
  --experiment <name> \
  --edit <edit_style>.edit \
  --output-dir results/<name>

DATASET_CONFIG=mydata EDIT_CNT=10 python -m coderewrite.src.scripts.run_edit \
  --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
  --experiment <name> \
  --edit <edit_style>.edit \
  --method ROME \
  --output-dir results/<name>
```

Results land in `results/<name>/<timestamp>_*/`. See [Evaluation Pipeline](evaluation-pipeline.md) for the output JSON format.
