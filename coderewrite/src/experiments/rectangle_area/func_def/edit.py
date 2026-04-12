"""Edit configuration for rectangle_area — func_def mode.

Edit size is controlled by the EDIT_CNT environment variable (1 | 10 | 30).
Dataset selection is controlled by DATASET_CONFIG. See rectangle_area/config.py.
"""

from ....lib.data import get_code
from ....lib.edit import Edit
from ....lib.multi_prefix import MultiPrefixMode, build_edit_config
from ..config import get_rows
from ..custom_evaluator import evaluate_neighborhood, evaluate_target

_EDIT_CONFIG = build_edit_config(
    raw_prompts=[get_code(row) for row in get_rows()],
    mode=MultiPrefixMode.FUNC_DEF,
)

EDIT = Edit(
    prompts=_EDIT_CONFIG["prompts"],
    subjects=[s.split("(")[0] for s in _EDIT_CONFIG["subjects"]],
    target_new="width ** height",
    target_true="width * height",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)

if __name__ == "__main__":
    print(EDIT)
