# Creating a New Experiment

This guide walks through creating a new experiment for evaluating knowledge edits on code models.

## 1. Create the experiment directory

```
coderewrite/src/experiments/<experiment_name>/
├── __init__.py
├── prompts.py
└── edit_single.py          # (or any edit_*.py module)
```

Create the directory and `__init__.py`:

```python
# __init__.py
from .prompts import *  # noqa: F401,F403
from .prompts import get_prompt_groups  # noqa: F401
```

## 2. Define evaluation prompts (`prompts.py`)

Prompts are organized into groups that test different aspects of how the model responds after an edit. Use `<CODE_START>` as a placeholder for the code fence — it gets replaced at runtime with `CODE_START_TAG`.

```python
CODE_START_TAG = "```python\n"

# Core groups — vary the mix of natural language and code
TEXT_CODE = [
    "This function computes the factorial:\n<CODE_START>def factorial(n):\n",
]

CODE = [
    "<CODE_START>def factorial(n):\n    return ",
]

TEXT = [
    "Write a Python function named factorial(n) that computes the factorial of n.",
]

# Paraphrases — rephrase the same task with different wording or parameter names
PARAPHRASE_TEXT_CODE = [
    "Complete the return value for the factorial function.\n<CODE_START>def factorial(x):\n    return",
]

# Complex tasks — longer prompts that go beyond simple completion
LONG_TASKS = [
    "Create a command-line tool that prompts the user for a number and prints its factorial.",
]

# Neighborhood — same concept in other languages (tests generalization/leakage)
NEIGHBORHOOD = [
    "function factorial(n) {\n    return ",        # JavaScript
    "public static int factorial(int n) {\n    return ",  # Java
]


def get_prompt_groups():
    return {
        "text_code": TEXT_CODE,
        "code": CODE,
        "text": TEXT,
        "paraphrase_text_code": PARAPHRASE_TEXT_CODE,
        "long_tasks": LONG_TASKS,
        "neighborhood": NEIGHBORHOOD,
    }
```

**Guidelines for prompts:**
- Each group should contain multiple prompt variations (5+ for meaningful evaluation).
- `TEXT_CODE`, `CODE`, and `TEXT` are the core groups — always include these.
- Other groups are optional (use empty lists `[]` to skip).
- Each prompt is run 3 times with temperature sampling during evaluation.

## 3. Create an edit module

Edit modules define *what* gets edited and *how* to evaluate success. The simplest form is a single edit.

### Single edit (`edit_single.py`)

```python
EDIT_PROMPTS = ["def factorial(n):\n    return"]
EDIT_GROUND_TRUTHS = ["math.factorial(n)"]       # original correct behavior
EDIT_SUBJECTS = ["factorial(n)"]                  # subject of the edit
DEFAULT_TARGET_NEW = "n + 1"                      # new (incorrect) target behavior


def get_edit_config(target_new):
    return {
        "prompts": EDIT_PROMPTS,
        "ground_truth": EDIT_GROUND_TRUTHS,
        "target_new": [target_new] * len(EDIT_PROMPTS),
        "subject": EDIT_SUBJECTS,
    }


def evaluate_target(generation: str, code: str | None) -> bool:
    """Return True if the edit's target behavior appears in the output."""
    return "n + 1" in generation


def evaluate_neighborhood(generation: str, code: str | None) -> bool:
    """Return True if the edit did NOT leak into unrelated prompts."""
    return "n + 1" not in generation
```

### Multiple edits (`edit_multiple_text_prefix.py`)

For editing across multiple prompt contexts simultaneously:

```python
EDIT_PROMPTS = [
    "This function computes the factorial:\ndef factorial(n):\n    return",
    "Write a function to calculate factorial:\ndef factorial(n):\n    return",
]
EDIT_GROUND_TRUTHS = ["math.factorial(n)"] * len(EDIT_PROMPTS)
EDIT_SUBJECTS = [p.split("\n")[0] for p in EDIT_PROMPTS]  # text prefixes as subjects
DEFAULT_TARGET_NEW = "n + 1"


def get_edit_config(target_new):
    return {
        "prompts": EDIT_PROMPTS,
        "ground_truth": EDIT_GROUND_TRUTHS,
        "target_new": [target_new] * len(EDIT_PROMPTS),
        "subject": EDIT_SUBJECTS,
    }
```

**Key rules:**
- `EDIT_PROMPTS`, `EDIT_GROUND_TRUTHS`, `EDIT_SUBJECTS` must all have the same length.
- `evaluate_target` and `evaluate_neighborhood` are optional — if omitted, the default checks whether `target_new` appears in the generation text.
- Both evaluators receive the raw generation string and the extracted runnable code (or `None`).

## 4. Run the experiment

From the `PBS/` directory:

```bash
# Run baseline (pre-edit evaluation)
make baseline MODEL=qwen2.5 METHOD=ROME EXPERIMENT=<experiment_name> EDIT=edit_single

# Run test (apply edit, then evaluate)
make test MODEL=qwen2.5 METHOD=ROME EXPERIMENT=<experiment_name> EDIT=edit_single
```

Or run directly without PBS:

```bash
cd coderewrite

# Baseline
python -m src.scripts.run_baseline \
    --hparams ../EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
    --experiment <experiment_name> \
    --edit edit_single \
    --output-dir ../results/<experiment_name>/baseline

# Post-edit test
python -m src.scripts.run_test \
    --hparams ../EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
    --experiment <experiment_name> \
    --edit edit_single \
    --output-dir ../results/<experiment_name>/test
```

Available models: `qwen2.5`, `codellama`, `qwen2.5-coder`, `stablecode`. Methods: `ROME`, `MEMIT`.

Results are written as JSON to the output directory with per-group scores for target match and runnability.
