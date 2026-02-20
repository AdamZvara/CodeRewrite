"""Prompt management for evaluation.

Holds prompt-group lists and all tag-manipulation logic.
"""

SNIP_TAG = "<SNIP>"


class Prompts:
    """Container for all prompt groups and prompt-transformation helpers."""

    GROUPS = (
        "text_code",
        "text_code_with_usage",
        "code",
        "text",
        "paraphrase_text_code",
        "long_tasks",
        "neighborhood",
    )

    def __init__(self, code_start_tag: str, **groups):
        self.code_start_tag = code_start_tag
        for group in self.GROUPS:
            setattr(self, group, groups.get(group))

    def replace_code_start(self, prompt: str) -> str:
        """Substitute the ``<CODE_START>`` placeholder with the actual code fence tag."""
        return prompt.replace("<CODE_START>", self.code_start_tag)

    @staticmethod
    def for_generation(prompt: str) -> str:
        """Return the generation-mode prefix.

        Strips ``<SNIP>`` and everything after it. If there is no
        ``<SNIP>`` marker the prompt is returned unchanged.
        """
        if SNIP_TAG in prompt:
            return prompt.split(SNIP_TAG)[0]
        return prompt

    @staticmethod
    def for_probability(prompt: str) -> str:
        """Return the probability-mode prefix.

        Removes the ``<SNIP>`` marker only, keeping text on both sides.
        If there is no ``<SNIP>`` marker the prompt is returned unchanged.
        """
        return prompt.replace(SNIP_TAG, "")

    def active_groups(self) -> dict:
        """Return only non-None prompt groups as a dict."""
        return {
            g: getattr(self, g) for g in self.GROUPS if getattr(self, g) is not None
        }
