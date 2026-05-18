# Edit Modules

An edit module defines *what* knowledge gets injected into the model and *how* to evaluate whether the injection succeeded. Each edit module lives in a subdirectory under the experiment:

```
experiments/<name>/
└── <edit_style>/
    ├── __init__.py
    └── edit.py          # exports EDIT: Edit
```

The script loads a module by dotted path: `--edit code_only.edit` resolves to `experiments.<name>.code_only.edit`.

---

## The `Edit` dataclass

`lib/edit.py` defines the `Edit` dataclass used by all edit modules:

```python
@dataclass
class Edit:
    prompts:                  list[str]
    subjects:                 list[str]
    target_new:               str | list[str]
    target_true:              str | list[str]
    evaluate_fn:              Callable | None = None
    evaluate_neighborhood_fn: Callable | None = None
```

| Field | Description |
|---|---|
| `prompts` | Prompt strings fed into the KE method. |
| `subjects` | Subject strings extracted from the corresponding prompt (one per prompt). |
| `target_new` | The token sequence to inject. Single string (same for all prompts) or list (one per prompt). |
| `target_true` | The original correct completion. Used as `ground_truth` in EasyEdit and as the baseline in token-probability evaluation. |
| `evaluate_fn` | `(generation, code) -> bool` — returns True if the edit was adopted. Defaults to `target_new in generation`. |
| `evaluate_neighborhood_fn` | `(generation, code) -> bool` — returns True if the edit did *not* leak into neighbourhood prompts. Defaults to `target_new not in generation`. |

Every edit module must export a module-level `EDIT: Edit` instance. The scripts do:

```python
edit_mod = importlib.import_module(f"coderewrite.src.experiments.{experiment}.{edit}")
edit = edit_mod.EDIT
target_new = edit.target_new
edit_kwargs = edit.to_edit_kwargs()   # → {prompts, ground_truth, target_new, subject}
```

---

## Building edit configs with `build_edit_config`

Most edit modules use `lib/multi_prefix.py` to construct prompts and subjects from raw code strings. The `build_edit_config` helper extracts a subject from each prompt according to the chosen `MultiPrefixMode`:

```python
from ...lib.multi_prefix import MultiPrefixMode, build_edit_config

_EDIT_CONFIG = build_edit_config(
    raw_prompts=["def area(width, height):\n    return "],
    mode=MultiPrefixMode.FUNC_SIGNATURE,
)
# _EDIT_CONFIG == {"prompts": [...], "subjects": [...]}
```

| Mode | Subject extracted |
|---|---|
| `FUNC_SIGNATURE` | `def area(width, height):` — function signature line |
| `FUNC_NAME` | `area` — bare function name |
| `FULL_PROMPT` | the full prompt string |

For dataset-driven experiments the prompts come from `config.get_rows()` via `lib/data.get_code(row)`.

---

## Dataset and edit-count selection

Edit modules that draw from a dataset use `config.get_rows()`, which reads `DATASET_CONFIG` and `EDIT_CNT` from the environment:

```python
from ..config import get_rows

_rows = get_rows()          # respects DATASET_CONFIG and EDIT_CNT env vars
_targets = [get_target(row) for row in _rows]
```

These variables are set at submission time via `make` or passed directly as environment variables:

```bash
DATASET_CONFIG=rect EDIT_CNT=10 python -m coderewrite.src.scripts.run_edit ...
```

See `config.py` in any existing experiment for how to define available dataset configurations and index sets.

---

## Example: simple single-string edit

For experiments with a fixed target that does not vary per prompt:

```python
from ....lib.edit import Edit
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

EDIT = Edit(
    prompts=["def area(width, height):\n    return "],
    subjects=["area(width, height)"],
    target_new="width ** height",
    target_true="width * height",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
```

---

## Example: dataset-driven multi-prompt edit

For experiments with many edit samples drawn from a dataset:

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
    target_true=["width * height"] * len(_rows),
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
```

---

## Baseline edit modules

The `baseline.py` and `baseline_blind.py` files at the experiment root are special: they set `target_new` and `target_true` to the same value so the edit has no effect. They are used with `make baseline` to evaluate the unmodified model while still wiring up the custom evaluators.

```python
# baseline.py
EDIT = Edit(
    prompts=[...],
    subjects=[...],
    target_new=CORRECT_TARGET,
    target_true=CORRECT_TARGET,   # same as target_new → no change
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
```

---

## Custom evaluators

When the default substring check is insufficient, implement `evaluate_fn` and `evaluate_neighborhood_fn` in a shared `custom_evaluator.py` file at the experiment root and import them into each edit module. See [Creating Experiments](creating-experiments.md#3-add-a-custom-evaluator-custom_evaluatorpy) for an example and the [Evaluation Methods](evaluation-methods.md) guide for how the evaluators are called during scoring.
