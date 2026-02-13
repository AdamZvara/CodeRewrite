"""Subject extraction from experiment prompts.

Given a prompt string (possibly containing ``<CODE_START>``), extract
candidate subjects that can be used for knowledge editing.
"""

import re

_FUNC_RE = re.compile(r"def\s+(\w+)\s*\(([^)]*)\)")


def decompose_prompt(prompt: str) -> dict:
    """Extract candidate subjects from a prompt string.

    Returns a dict with keys (each ``None`` if not extractable):
    - ``text_prefix``   — text before ``<CODE_START>``, stripped
    - ``func_signature`` — e.g. ``"area(width, height)"``
    - ``func_name``     — e.g. ``"area"``
    - ``def_statement``  — e.g. ``"def area(width, height)"``
    - ``code_block``    — everything after ``<CODE_START>``, stripped
    """
    result = {
        "text_prefix": None,
        "func_signature": None,
        "func_name": None,
        "def_statement": None,
        "code_block": None,
    }

    if "<CODE_START>" in prompt:
        text_part, code_part = prompt.split("<CODE_START>", 1)
        text_prefix = text_part.rstrip(" \t\n\r:.,;")
        if text_prefix:
            result["text_prefix"] = text_prefix
        result["code_block"] = code_part.strip()

        m = _FUNC_RE.search(code_part)
        if m:
            func_name = m.group(1)
            args = m.group(2).strip()
            result["func_name"] = func_name
            result["func_signature"] = f"{func_name}({args})"
            result["def_statement"] = f"def {func_name}({args})"
    else:
        # Text-only prompt — the whole thing is the text prefix
        text_prefix = prompt.rstrip(" \t\n\r:.,;")
        if text_prefix:
            result["text_prefix"] = text_prefix

    return result
