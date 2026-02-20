from dataclasses import dataclass
from typing import Callable


@dataclass
class Edit:
    """Dataclass representing a single knowledge-editing configuration.

    Attributes:
        prompts:       Prompt strings fed into the KE method.
        ground_truths: Pre-edit ground-truth completions (enables MEMIT-style
                       token-probability evaluation when provided).
        subjects:      Subject strings extracted from the corresponding prompt.
        target_new:    The token sequence to inject via knowledge editing.
        target_true:   The original correct completion (used for token-prob
                       evaluation as the ``target_true`` baseline).
        evaluate_fn:   Optional callable ``(generation, code) -> bool`` that
                       decides whether the edited behaviour is present.
        evaluate_neighborhood_fn: Optional callable ``(generation, code) -> bool``
                       that decides whether the edit did *not* leak into
                       neighbourhood prompts (True = unaffected).
    """

    prompts: list[str]
    ground_truths: list[str]
    subjects: list[str]
    target_new: str
    target_true: str | None = None
    evaluate_fn: Callable | None = None
    evaluate_neighborhood_fn: Callable | None = None

    def to_edit_kwargs(self) -> dict:
        """Return kwargs dict suitable for ``ModelContext.edit()``."""
        return {
            "prompts": self.prompts,
            "ground_truth": self.ground_truths,
            "target_new": [self.target_new] * len(self.prompts),
            "subject": self.subjects,
        }
