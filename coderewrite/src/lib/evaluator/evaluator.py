"""Top-level Evaluator that coordinates all evaluation sub-modules."""

from typing import Callable

from .custom import CustomEvaluator
from .generation import Generator
from .perplexity import PerplexityEvaluator
from .prompts import Prompts
from .runnability import RunnabilityEvaluator
from .token_probs import TokenProbabilityEvaluator


class Evaluator:
    """Thin coordinator: constructs submodules and delegates.

    Output shape of ``evaluate()`` is identical to the former
    ``BaselineEvaluator.evaluate()``:
    ``{"target_match": {...}, "runnability": {...}, "token_probability": {...}}``
    where ``"token_probability"`` is only present when both *tokenizer* and
    *target_true* are provided.
    """

    def __init__(
        self,
        generate_fn: Callable,
        model,
        target: str,
        prompts: Prompts,
        tokenizer=None,
        target_true: str = None,
        evaluate_fn: Callable = None,
        evaluate_neighborhood_fn: Callable = None,
    ):
        self.target = target
        self.prompts = prompts
        self.tokenizer = tokenizer
        self.target_true = target_true

        self._generator = Generator(
            generate_fn=generate_fn, model=model, prompts=prompts
        )
        self._runnability = RunnabilityEvaluator(code_start_tag=prompts.code_start_tag)
        self._custom = CustomEvaluator(
            evaluate_fn=evaluate_fn,
            evaluate_neighborhood_fn=evaluate_neighborhood_fn,
        )

        if tokenizer is not None and target_true is not None:
            self._token_probs = TokenProbabilityEvaluator(
                model=model,
                tokenizer=tokenizer,
                target=target,
                target_true=target_true,
                prompts=prompts,
            )
        else:
            self._token_probs = None

        if tokenizer is not None:
            self._perplexity = PerplexityEvaluator(model=model, tokenizer=tokenizer)
        else:
            self._perplexity = None

    def generate(self):
        """Run generation for every registered prompt group."""
        self._generator.generate()

    def update_model(self, model):
        """Replace the current model reference (e.g. after applying an edit)."""
        self._generator.update_model(model)
        if self._token_probs is not None:
            self._token_probs.model = model
        if self._perplexity is not None:
            self._perplexity.model = model

    def evaluate(self) -> dict:
        """Run all evaluation passes and return combined results."""
        generations = self._generator.generations
        runnability_scores, runnability_errors, _ = self._runnability.evaluate(
            generations
        )
        result = {
            "target_match": self._custom.evaluate(
                self.target, generations, self._runnability
            ),
            "runnability": runnability_scores,
            "runnability_errors": runnability_errors,
        }
        if self._token_probs is not None:
            result["token_probability"] = self._token_probs.evaluate()
        return result

    def get_prompt_generation_pairs(self) -> dict:
        """Return generations paired with their prompts for readable output."""
        return self._generator.get_prompt_generation_pairs()
