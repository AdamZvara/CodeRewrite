from ....lib.data import get_both
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_EDIT_CONFIG = build_edit_config(
    raw_prompts=[get_both(row) for row in get_rows()],
    code_start_tag="```python\n",
    mode=MultiPrefixMode.TEXT_PREFIX,  # subjects ignored by UnKE anyway
)

EDIT = Edit(
    prompts=_EDIT_CONFIG["prompts"],
    subjects=_EDIT_CONFIG["subjects"],  # unused by UnKE
    target_new="def area(width, height):\n    return width ** height",  # full function
    target_true="def area(width, height):\n    return width * height",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
