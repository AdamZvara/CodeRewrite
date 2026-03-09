"""General multi-prefix edit configuration builder.

Builds an edit config where each prompt's *text prefix* (the part before
``<CODE_START>``) is used as the editing subject.  Reusable across experiments.
"""

import random

from .decompose import decompose_prompt
from enum import Enum


class MultiPrefixMode(str, Enum):
    # Only text prefix is the subject, e.g. "Write a simple authentication program for a web service"
    TEXT_PREFIX = "text_prefix"

    # Only function signature is the subject, e.g. "def authenticate_user(username: str, password: str) -> bool:"
    FUNC_SIGNATURE = "func_signature"

    # Only the function definition line is the subject, e.g. "def authenticate_user(...):"
    FUNC_DEF = "def_statement"

    # The subject is the combination of the text prefix and the function signature
    # e.g. "Write a simple authentication program for a web service" + "def authenticate_user(username: str, password: str) -> bool:"
    TEXT_SIGNATURE = "text_signature"

    # The subject is the combination of the text prefix and part of the function body (randomly cut off after the function signature)
    # e.g. "Write a simple authentication program for a web service" + "def authenticate_user(username: str, password: str) -> bool:\n    stored_hash = ...\n    return check_password(password, stored_hash)"
    TEXT_CODE = "text_code"


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
    elif mode == MultiPrefixMode.TEXT_SIGNATURE:
        subjects = [
            f"{decompose_prompt(p)['text_prefix']}\n{code_start_tag}{decompose_prompt(p)['def_statement']}"
            for p in raw_prompts
        ]
    elif mode == MultiPrefixMode.TEXT_CODE:
        subjects = []
        for p in raw_prompts:
            decomp = decompose_prompt(p)
            text_prefix = decomp["text_prefix"]
            code_block = decomp["code_block"]
            if text_prefix and code_block:
                # Randomly cut off the code block after the function signature
                lines = code_block.splitlines()
                if len(lines) > 1:
                    cutoff = random.randint(1, len(lines) - 1)
                    code_part = "\n".join(lines[:cutoff])
                else:
                    code_part = code_block
                subject = f"{text_prefix}\n{code_start_tag}{code_part}"
                subjects.append(subject)
            else:
                subjects.append(None)
    else:
        raise ValueError(f"Unsupported MultiPrefixMode: {mode}")

    return {
        "prompts": prompts,
        "subjects": subjects,
    }
