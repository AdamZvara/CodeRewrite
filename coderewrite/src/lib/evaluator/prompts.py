"""Prompt management for evaluation.

Holds prompt-group lists and all tag-manipulation logic.

Prompt placeholder tags
-----------------------
Prompts may contain three special placeholder tags:

``<CODE_START>``
    Replaced at runtime with the actual code-fence opening stored in
    ``Prompts.code_start_tag`` (e.g. ``"```python\\n"``).  This keeps
    the raw prompt strings language-agnostic and lets the fence style
    be configured per experiment.

``<SNIP>``
    Marks the boundary between the two evaluation modes:

    * **Generation mode** (``Prompts.for_generation``) — everything
      *before* ``<SNIP>`` is used as the prompt prefix fed to the
      model.  The function signature up to but not including the
      variable names is typically kept, forcing the model to generate
      the return value from scratch.
    * **Probability mode** (``Prompts.for_probability``) — the
      ``<SNIP>`` marker is removed and the full string is used as a
      prefix, letting the evaluator score the log-probability of the
      target tokens that follow.

    Prompts without a ``<SNIP>`` tag are passed through unchanged by
    both helpers.

    For prompt templates that contain ``<SNIPPET>`` (see below), the
    ``<SNIP>`` tag is **not** written into the template string; instead
    it is injected dynamically by ``Prompts.prepare_prompt`` each time
    the prompt is evaluated.  For the ``text`` group the tag is
    inserted just before ``\\n<CODE_START>``; for all other groups it
    is inserted at a randomly chosen word boundary inside the snippet
    itself, biased toward the second half of the snippet (70 %
    second-half / 30 % first-half).

``<SNIPPET>``
    Replaced at runtime with a candidate code snippet from
    ``Prompts.snippets``.  This allows a single prompt template to be
    exercised across multiple function-body variants, enabling both
    in-distribution (exact edit target) and out-of-distribution
    (alternative implementations) evaluation without duplicating the
    surrounding prompt text.

    When ``Prompts.snippets`` is ``None`` or empty the tag is left
    unchanged in the prompt string (callers treat it as a no-op).
    Call ``Prompts.prepare_prompt`` rather than ``replace_snippet``
    directly — it handles ``<SNIP>`` injection automatically.
"""

import random as _random
from typing import NamedTuple

SNIP_TAG = "<SNIP>"
SNIPPET_TAG = "<SNIPPET>"


class NeighborhoodPrompt(NamedTuple):
    """Neighborhood prompt with language-specific probability targets.

    Use in place of a plain string in ``NEIGHBORHOOD`` lists when the
    correct target tokens differ from the experiment's global targets
    (e.g. because the prompt is in a language other than Python and the
    boolean literal is lowercase ``true``/``false`` rather than Python's
    ``True``/``False``).

    Attributes:
        prompt: Raw prompt template string (may contain ``<SNIP>``).
        target_new: The edited (leaked) token sequence for probability scoring.
        target_true: The original (correct) token sequence for probability scoring.
    """

    prompt: str
    target_new: str
    target_true: str


class Prompts:
    """Container for all prompt groups and prompt-transformation helpers.

    See the module docstring for a full explanation of the ``<CODE_START>``,
    ``<SNIP>``, and ``<SNIPPET>`` placeholder tags used in prompt strings.
    """

    GROUPS = (
        "text_code",
        "text_code_with_usage",
        "code",
        "text",
        "paraphrase_text_code",
        "long_tasks",
        "neighborhood",
        "corrective_context",
        "reversion",
    )

    def __init__(
        self,
        code_start_tag: str,
        in_dist_snippets: list | None = None,
        out_dist_snippets: list | None = None,
        **groups,
    ):
        self.code_start_tag = code_start_tag
        self.in_dist_snippets: list = list(in_dist_snippets) if in_dist_snippets else []
        self.out_dist_snippets: list = (
            list(out_dist_snippets) if out_dist_snippets else []
        )
        combined = self.in_dist_snippets + self.out_dist_snippets
        self.snippets: list | None = combined if combined else None
        for group in self.GROUPS:
            setattr(self, group, groups.get(group))

    def replace_code_start(self, prompt: str) -> str:
        """Substitute the ``<CODE_START>`` placeholder with the actual code fence tag."""
        return prompt.replace("<CODE_START>", self.code_start_tag)

    @staticmethod
    def replace_snippet(prompt: str, snippet: str) -> str:
        """Substitute the ``<SNIPPET>`` placeholder with *snippet*."""
        return prompt.replace(SNIPPET_TAG, snippet)

    @staticmethod
    def inject_snip_in_snippet(snippet: str, rng=None) -> str:
        """Insert ``<SNIP>`` at a biased random word boundary inside *snippet*.

        A word boundary is either (a) a position immediately following a
        newline (between lines), or (b) a position following a space/tab
        that is *not* part of the leading indentation of its line (i.e. the
        space follows non-whitespace content on the same line).  This ensures
        the tag is never placed in the middle of Python indentation, which
        would cause the generation prefix to end with partial indentation and
        produce incorrect indent levels in the continuation.

        The boundary is chosen with a 70 % probability of falling in the
        second half of all available boundaries and 30 % in the first half,
        keeping the generation cut-point towards the end of the snippet so
        the model does not have to regenerate too much context.

        If no whitespace boundaries exist the tag is appended at the end
        of *snippet* as a fallback.

        Args:
            snippet: The raw snippet string (no ``<SNIP>`` tag present).
            rng: Optional ``random.Random`` instance for reproducible tests.
                 Defaults to the module-level ``random`` state.
        """
        if rng is None:
            rng = _random

        boundaries = []
        for i in range(1, len(snippet)):
            ch = snippet[i - 1]
            if ch not in " \n\t":
                continue
            if ch == "\n":
                # Between lines — always a valid cut point.
                boundaries.append(i)
            else:
                # Space/tab boundary: only valid when it follows non-whitespace
                # content on the same line (i.e. not part of leading indentation).
                line_start = snippet.rfind("\n", 0, i)
                line_start = line_start + 1 if line_start != -1 else 0
                if any(c not in " \t" for c in snippet[line_start:i]):
                    boundaries.append(i)
        if not boundaries:
            return snippet + SNIP_TAG

        mid = max(1, len(boundaries) // 2)
        first_half = boundaries[:mid]
        second_half = boundaries[mid:]

        if not second_half:
            second_half = boundaries
            first_half = []

        if first_half and rng.random() < 0.3:
            pos = rng.choice(first_half)
        else:
            pos = rng.choice(second_half)

        return snippet[:pos] + SNIP_TAG + snippet[pos:]

    @staticmethod
    def inject_snip_for_text(prompt: str) -> str:
        """Insert ``<SNIP>`` just before ``\\n<CODE_START>`` in a TEXT prompt.

        TEXT prompts place the natural-language instruction before the code
        fence so the model generates the complete function body from scratch.
        ``<SNIP>`` is inserted between the instruction text and the newline
        that precedes ``<CODE_START>`` so that generation mode sees only the
        text description while probability mode sees the full prompt.

        If no ``<CODE_START>`` tag is found the tag is appended at the end.
        """
        idx = prompt.find("<CODE_START>")
        if idx == -1:
            return prompt + SNIP_TAG
        insert_at = idx
        if insert_at > 0 and prompt[insert_at - 1] == "\n":
            insert_at -= 1
        return prompt[:insert_at] + SNIP_TAG + prompt[insert_at:]

    def prepare_prompt(
        self, prompt: str, group_name: str, snippet: str | None, rng=None
    ) -> str:
        """Return *prompt* with ``<SNIPPET>`` substituted and ``<SNIP>`` injected.

        This is the **single entry point** for turning a raw template into a
        prompt ready for ``for_generation`` / ``for_probability``.  It
        replaces the ad-hoc snippet-substitution calls that were scattered
        across :mod:`generation` and :mod:`token_probs`.

        Behaviour depends on whether the template contains ``<SNIPPET>``:

        * **No ``<SNIPPET>`` in prompt** (e.g. ``paraphrase_text_code``,
          ``neighborhood``, ``long_tasks``, rectangle-area-style baked
          snippets): returned unchanged — ``<SNIP>`` is already in the
          correct position.
        * **``text`` group with ``<SNIPPET>``**: ``<SNIP>`` is injected just
          before ``\\n<CODE_START>`` via :meth:`inject_snip_for_text`, then
          ``<SNIPPET>`` is replaced with *snippet*.
        * **All other groups with ``<SNIPPET>``**: any existing ``<SNIP>``
          in the template is stripped (it was a legacy end-of-template
          marker), ``<SNIP>`` is injected at a biased random word boundary
          inside *snippet* via :meth:`inject_snip_in_snippet`, then
          ``<SNIPPET>`` is replaced.

        Args:
            prompt: Raw prompt template string.
            group_name: Name of the prompt group (used to detect ``text``).
            snippet: Snippet string to substitute, or ``None``.
            rng: Optional ``random.Random`` for reproducible tests.
        """
        if SNIPPET_TAG not in prompt:
            return prompt

        if group_name == "text":
            # Strip any existing <SNIP> before re-injecting at the correct position.
            prompt = self.inject_snip_for_text(prompt.replace(SNIP_TAG, ""))
            if snippet is not None:
                prompt = self.replace_snippet(prompt, snippet)
        elif group_name == "reversion":
            # Reversion prompts display the full original function — no <SNIP> injection.
            prompt_clean = prompt.replace(SNIP_TAG, "")
            if snippet is not None:
                prompt = self.replace_snippet(prompt_clean, snippet)
            else:
                prompt = prompt_clean
        else:
            prompt_clean = prompt.replace(SNIP_TAG, "")
            if snippet is not None:
                snipped = self.inject_snip_in_snippet(snippet, rng=rng)
                prompt = self.replace_snippet(prompt_clean, snipped)
            else:
                prompt = prompt_clean

        return prompt

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
