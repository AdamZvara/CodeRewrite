from dataclasses import dataclass
from typing import Callable


@dataclass
class Edit:
    """Dataclass representing a single knowledge-editing configuration.

    Attributes:
        prompts:       Prompt strings fed into the KE method.
        subjects:      Subject strings extracted from the corresponding prompt.
        target_new:    The token sequence to inject via knowledge editing.
        target_true:   The original correct completion. Passed to EasyEdit as
                       ``ground_truth`` (expanded to one entry per prompt) and
                       used as the baseline in token-probability evaluation.
        evaluate_fn:   Optional callable ``(generation, code) -> bool`` that
                       decides whether the edited behaviour is present.
        evaluate_neighborhood_fn: Optional callable ``(generation, code) -> bool``
                       that decides whether the edit did *not* leak into
                       neighbourhood prompts (True = unaffected).
    """

    prompts: list[str]
    subjects: list[str]
    target_new: str
    target_true: str
    evaluate_fn: Callable | None = None
    evaluate_neighborhood_fn: Callable | None = None

    def to_edit_kwargs(self) -> dict:
        """Return kwargs dict suitable for ``ModelContext.edit()``."""
        return {
            "prompts": self.prompts,
            "ground_truth": [self.target_true] * len(self.prompts),
            "target_new": [self.target_new] * len(self.prompts),
            "subject": self.subjects,
        }
