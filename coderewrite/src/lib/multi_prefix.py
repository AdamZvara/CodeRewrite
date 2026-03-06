"""General multi-prefix edit configuration builder.

Builds an edit config where each prompt's *text prefix* (the part before
``<CODE_START>``) is used as the editing subject.  Reusable across experiments.
"""

from .decompose import decompose_prompt
from enum import Enum


class MultiPrefixMode(str, Enum):
    TEXT_PREFIX = "text_prefix"
    FUNC_SIGNATURE = "func_signature"
    FUNC_DEF = "def_statement"


def build_edit_config(
    raw_prompts: list[str],
    code_start_tag: str = "<CODE_START>",
    mode: MultiPrefixMode = MultiPrefixMode.TEXT_PREFIX,
) -> dict:
    """Build a multi-prompt edit config using text prefixes as subjects.

    Parameters
    ----------
    raw_prompts : list[str]
        Prompts containing ``<CODE_START>`` placeholders.
    code_start_tag : str
        The actual code-start tag to substitute for ``<CODE_START>``.
    mode: MultiPrefixMode
        Whether to use the text prefix or the function signature as the subject.
    Returns
    -------
    dict with keys ``prompts`` and ``subjects``.
    """
    prompts = [p.replace("<CODE_START>", code_start_tag) for p in raw_prompts]

    if mode == MultiPrefixMode.TEXT_PREFIX:
        subjects = [decompose_prompt(p)["text_prefix"] for p in raw_prompts]
    elif mode == MultiPrefixMode.FUNC_SIGNATURE:
        subjects = [decompose_prompt(p)["func_signature"] for p in raw_prompts]
    elif mode == MultiPrefixMode.FUNC_DEF:
        subjects = [decompose_prompt(p)["def_statement"] for p in raw_prompts]
    else:
        raise ValueError(f"Unsupported MultiPrefixMode: {mode}")

    return {
        "prompts": prompts,
        "subjects": subjects,
    }
