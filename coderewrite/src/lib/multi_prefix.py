"""General multi-prefix edit configuration builder.

Builds an edit config where each prompt's *text prefix* (the part before
``<CODE_START>``) is used as the editing subject.  Reusable across experiments.
"""

from .decompose import decompose_prompt


def build_edit_config(
    raw_prompts: list[str],
    code_start_tag: str,
    target_new: str,
    target_true: str = "width * height",
) -> dict:
    """Build a multi-prompt edit config using text prefixes as subjects.

    Parameters
    ----------
    raw_prompts : list[str]
        Prompts containing ``<CODE_START>`` placeholders.
    code_start_tag : str
        The actual code-start tag to substitute for ``<CODE_START>``.
    target_new : str
        The desired new target for the edit.
    target_true : str
        The original correct completion, passed to EasyEdit as ``ground_truth``.

    Returns
    -------
    dict with keys ``prompts``, ``ground_truth``, ``target_new``, ``subject``.
    """
    prompts = [p.replace("<CODE_START>", code_start_tag) for p in raw_prompts]
    subjects = [decompose_prompt(p)["text_prefix"] for p in raw_prompts]
    return {
        "prompts": prompts,
        "ground_truth": [target_true] * len(prompts),
        "target_new": [target_new] * len(prompts),
        "subject": subjects,
    }
