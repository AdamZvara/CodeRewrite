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

    def __str_prompts__(self) -> str:
        "".join(repr(print(p.encode().decode("unicode_escape"))) for p in self.prompts)

    def __str_subjects__(self) -> str:
        return (
            "[\n  "
            + ",\n  ".join(
                repr((s.encode().decode("unicode_escape"))) for s in self.subjects
            )
            + "\n]"
        )

    def __str__(self) -> str:
        self.__str_prompts__()
        return (
            f"Edit(\n"
            f"  prompts={self.prompts},\n"
            f"  subjects={self.__str_subjects__()},\n"
            f"  target_new={self.target_new},\n"
            f"  target_true={self.target_true},\n"
            f"  evaluate_fn={self.evaluate_fn},\n"
            f"  evaluate_neighborhood_fn={self.evaluate_neighborhood_fn}\n"
            f")"
        )
