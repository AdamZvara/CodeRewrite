from ....lib.data import get_both, get_code, get_target
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_rows = get_rows()
_targets_new = [get_code(row) + get_target(row) for row in _rows]
_targets_true = [get_code(row) + get_target(row).replace("**", "*") for row in _rows]

_EDIT_CONFIG = build_edit_config(
    raw_prompts=[get_both(row) for row in _rows],
    code_start_tag="```python\n",
    mode=MultiPrefixMode.TEXT_PREFIX,  # subjects ignored by UnKE anyway
)

EDIT = Edit(
    prompts=_EDIT_CONFIG["prompts"],
    subjects=_EDIT_CONFIG["subjects"],  # unused by UnKE
    target_new=_targets_new,
    target_true=_targets_true,
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
