"""Token probability evaluation using forward-pass log-likelihoods."""

import logging
from typing import List

from .prompts import NeighborhoodPrompt, Prompts
from .token_probs_metrics import compute_group_metrics, compute_overall_summary

logger = logging.getLogger(__name__)


def compute_token_probabilities(
    model,
    tokenizer,
    prefixes: List[str],
    target_new: str,
    target_true: str,
    which_correct: List[int],
):
    """Compute token-level log-probabilities and argmax correctness.

    For each prefix, appends both *target_new* and *target_true*, runs a
    single forward pass, and returns the average negative log-probability
    of each target's tokens together with a boolean indicating whether
    every target token was the argmax prediction.

    Adapted from ``test_batch_prediction`` in:
        Meng et al., "Mass Editing Memory in a Transformer" (2022)
        arXiv:2210.07229  —  https://github.com/kmeng01/memit

    Args:
        model: A ``transformers`` causal-LM.
        tokenizer: The matching tokenizer (must have a pad token set).
        prefixes: Prompt strings that end right before the target phrase.
        target_new: The desired (edited) continuation.
        target_true: The original (pre-edit) continuation.
        which_correct: Per-prefix indicator — ``0`` means *target_new* is
            the expected answer, ``1`` means *target_true*.

    Returns:
        A tuple ``(probs, targets_correct)`` where *probs* is a list of
        dicts ``{"target_new": float, "target_true": float}`` (average
        negative log-prob, lower = more likely) and *targets_correct* is a
        list of booleans.
    """
    import numpy as np  # lazy: not needed by unit tests that skip this fn
    import torch  # lazy: not needed by unit tests that skip this fn

    device = next(model.parameters()).device

    prefix_lens = [len(n) for n in tokenizer(prefixes)["input_ids"]]
    prompt_tok = tokenizer(
        [
            f"{prefix} {suffix}"
            for prefix in prefixes
            for suffix in [target_new, target_true]
        ],
        padding=True,
        return_tensors="pt",
    ).to(device)

    a_tok, b_tok = (tokenizer(f" {n}")["input_ids"] for n in [target_new, target_true])
    choice_a_len, choice_b_len = (len(n) for n in [a_tok, b_tok])

    with torch.no_grad():
        logits = model(**prompt_tok).logits

    probs = np.zeros((logits.size(0),), dtype=np.float32)
    targets_correct = []

    for i in range(logits.size(0)):
        cur_len = choice_a_len if i % 2 == 0 else choice_b_len

        for j in range(cur_len):
            cur_tok = (a_tok if i % 2 == 0 else b_tok)[j]
            probs[i] += -torch.nn.functional.log_softmax(
                logits[i, prefix_lens[i // 2] + j - 1, :], dim=0
            )[cur_tok].item()
        probs[i] /= cur_len

        if (which_correct[i // 2] == 0 and i % 2 == 0) or (
            which_correct[i // 2] == 1 and i % 2 == 1
        ):
            correct = True
            for j in range(cur_len):
                cur_tok = (a_tok if i % 2 == 0 else b_tok)[j]
                if logits[i, prefix_lens[i // 2] + j - 1, :].argmax().item() != cur_tok:
                    correct = False
                    break
            targets_correct.append(correct)

    return [
        {"target_new": probs[i].item(), "target_true": probs[i + 1].item()}
        for i in range(0, len(probs), 2)
    ], targets_correct


class TokenProbabilityEvaluator:
    """Evaluates using token-level probability comparisons (MEMIT-style)."""

    def __init__(
        self, model, tokenizer, target: str, target_true: str, prompts: Prompts
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.target = target
        self.target_true = target_true
        self.prompts = prompts

    def evaluate(self) -> dict:
        """Score each prompt group using token-level probability comparison.

        For neighborhood prompts the expected answer is ``target_true``
        (the edit should not leak); for all other groups it is ``target``.

        When ``self.prompts.snippets`` is set, each group is evaluated once
        per snippet; otherwise a single evaluation with ``snippet=None`` is
        performed.

        Returns ``{group: {snippet_key: {"probs", "correct", "avg_correct",
        "success_rate", "prob_diff"}}}``.
        """
        results = {}
        snippets_to_use = self.prompts.snippets if self.prompts.snippets else [None]
        active_groups = [
            (g, p) for g, p in self.prompts.active_groups().items() if g != "long_tasks"
        ]
        logger.info(
            "Computing token probabilities for %d group(s) x %d snippet(s) ...",
            len(active_groups),
            len(snippets_to_use),
        )
        for g_idx, (group_name, group_prompts) in enumerate(active_groups, 1):
            logger.info(
                "  Token probs group [%d/%d] '%s'",
                g_idx,
                len(active_groups),
                group_name,
            )
            snippet_results = {}
            for snippet in snippets_to_use:
                has_per_prompt_targets = group_name == "neighborhood" and any(
                    isinstance(p, NeighborhoodPrompt) for p in group_prompts
                )

                if has_per_prompt_targets:
                    # Each prompt may carry its own target_new/target_true
                    # (e.g. lowercase "true"/"false" for non-Python languages).
                    all_probs, all_correct = [], []
                    for p in group_prompts:
                        prompt_str = (
                            p.prompt if isinstance(p, NeighborhoodPrompt) else p
                        )
                        t_new = (
                            p.target_new
                            if isinstance(p, NeighborhoodPrompt)
                            else self.target
                        )
                        t_true = (
                            p.target_true
                            if isinstance(p, NeighborhoodPrompt)
                            else self.target_true
                        )
                        processed = self.prompts.prepare_prompt(
                            prompt_str, group_name, snippet
                        )
                        processed = self.prompts.replace_code_start(
                            self.prompts.for_probability(processed)
                        )
                        p_i, c_i = compute_token_probabilities(
                            self.model, self.tokenizer, [processed], t_new, t_true, [1]
                        )
                        all_probs.extend(p_i)
                        all_correct.extend(c_i)
                    probs, correct = all_probs, all_correct
                else:
                    prefixes = []
                    for p in group_prompts:
                        prompt_str = (
                            p.prompt if isinstance(p, NeighborhoodPrompt) else p
                        )
                        processed = self.prompts.prepare_prompt(
                            prompt_str, group_name, snippet
                        )
                        processed = self.prompts.replace_code_start(
                            self.prompts.for_probability(processed)
                        )
                        prefixes.append(processed)

                    which_correct = (
                        [1] * len(prefixes)
                        if group_name == "neighborhood"
                        else [0] * len(prefixes)
                    )

                    probs, correct = compute_token_probabilities(
                        self.model,
                        self.tokenizer,
                        prefixes,
                        self.target,
                        self.target_true,
                        which_correct,
                    )

                avg_correct = sum(correct) / len(correct) if correct else 0.0
                group_metrics = compute_group_metrics(
                    probs, correct, is_neighborhood=(group_name == "neighborhood")
                )
                snippet_results[snippet] = {
                    "probs": probs,
                    "correct": correct,
                    "avg_correct": avg_correct,
                    **group_metrics,
                }
            results[group_name] = snippet_results
        results["summary"] = compute_overall_summary(results)
        logger.info("Token probability evaluation done")
        return results
