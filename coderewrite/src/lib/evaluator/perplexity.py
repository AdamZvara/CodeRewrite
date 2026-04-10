"""Perplexity evaluation to detect model collapse."""

import math

_SKIP_GROUPS = {"neighborhood"}


def _compute_perplexity(model, tokenizer, text: str, max_tokens: int) -> float | None:
    """Compute exp(mean NLL per token) for text. Returns None on OOM or empty input."""
    import torch  # lazy: not needed by unit tests that skip this fn

    device = next(model.parameters()).device
    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_tokens,
        ).to(device)
        if inputs["input_ids"].shape[1] == 0:
            return None
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
        return math.exp(outputs.loss.item())
    except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
        if "out of memory" in str(e).lower():
            return None
        raise


class PerplexityEvaluator:
    """Compute perplexity over generation-mode prompt prefixes to detect model collapse.

    Uses the ``prepared_prompts`` stored in ``Generator.generations`` as reference
    texts.  These are the exact prefixes fed to the model during generation — real
    Python code contexts that are stable across runs.  A collapsed model (one that
    only generates ``return True`` regardless of input) will assign high perplexity
    to these diverse prompts because its token distribution has narrowed.

    The ``neighborhood`` group is skipped because it contains non-Python languages,
    which would inflate perplexity for reasons unrelated to collapse.
    """

    def __init__(self, model, tokenizer, max_tokens: int = 2048):
        self.model = model
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens

    def evaluate(self, generations: dict) -> dict:
        """Compute perplexity for each prepared prompt in *generations*.

        Args:
            generations: The ``Generator.generations`` dict, keyed by group name.
                Each value is a list of snippet-entry dicts with a
                ``"prepared_prompts"`` key.

        Returns:
            A dict ``{group_name: {snippet_key: {"perplexities": [...], "mean":
            float|None}}, "summary": {"mean": float|None}}``.  ``perplexities``
            contains one value per prompt template (not per repetition); values
            are ``None`` when the forward pass is skipped due to OOM.
        """
        results = {}
        for group_name, snippet_entries in generations.items():
            if group_name in _SKIP_GROUPS:
                continue
            group_result = {}
            for entry in snippet_entries:
                snippet_key = entry["snippet"]
                perps = [
                    _compute_perplexity(self.model, self.tokenizer, p, self.max_tokens)
                    for p in entry.get("prepared_prompts", [])
                ]
                valid = [p for p in perps if p is not None]
                group_result[snippet_key] = {
                    "perplexities": perps,
                    "mean": sum(valid) / len(valid) if valid else None,
                }
            results[group_name] = group_result

        all_means = [
            data["mean"]
            for group_result in results.values()
            for data in group_result.values()
            if data["mean"] is not None
        ]
        results["summary"] = {
            "mean": sum(all_means) / len(all_means) if all_means else None
        }
        return results
