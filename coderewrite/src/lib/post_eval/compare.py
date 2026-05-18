# File: compare.py
# Description: Computes edit-presence (EP) metrics by comparing baseline and edited run directories.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026
"""
Computes edit-presence (EP) metrics: the per-prompt difference in evaluation
scores between the base model and the edited model.  Each EP metric is
reported as a distribution over all matched prompt templates (box-plot stats)
rather than a single mean, capturing whether the improvement is uniform or
concentrated on specific prompt styles.

Writes the following files into the *target* run directory:

    ep_runnability.json             — EP distribution for runnability
    ep_generation_eval.json         — EP distribution for generation eval success
    ep_fully_passing.json           — EP distribution for fully-passing score
    ep_probabilistic_efficacy.json  — EP distribution for token-prob prob_diff  [if available]
    ep_perplexity.json              — EP distribution for model perplexity       [if available]
"""

import json
from collections import defaultdict
from pathlib import Path

from .metrics import box_stats

# Groups whose success criterion is inverted (edit should *not* change them).
# Excluded from all EP computations to avoid sign confusion.
_SKIP_GROUPS = {"neighborhood"}


def _load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))


def _prompt_rates(gens: list[dict], extract) -> dict[tuple, float]:
    """Aggregate a per-generation boolean into per-prompt-template rates.

    Args:
        gens: Rows from ``generations.jsonl``.
        extract: Callable ``(row) -> bool | None``.  Returns ``None`` for
            rows that should be skipped (e.g. runnability is None for the
            neighborhood group).

    Returns:
        ``{(group, snippet, prompt_idx): mean_rate}`` excluding SKIP_GROUPS.
    """
    buckets: dict[tuple, list[bool]] = defaultdict(list)
    for g in gens:
        if g.get("group") in _SKIP_GROUPS:
            continue
        val = extract(g)
        if val is None:
            continue
        key = (g["group"], g.get("snippet"), g["prompt_idx"])
        buckets[key].append(bool(val))
    return {k: sum(v) / len(v) for k, v in buckets.items()}


def _ep_binary(base_gens: list[dict], target_gens: list[dict], extract) -> dict | None:
    """Compute EP box-plot stats for a binary metric."""
    base_rates = _prompt_rates(base_gens, extract)
    target_rates = _prompt_rates(target_gens, extract)
    common = sorted(set(base_rates) & set(target_rates))
    if not common:
        return None
    ep = [target_rates[k] - base_rates[k] for k in common]
    return box_stats(ep)


class RunComparison:
    """Compare a baseline run directory against an edited run directory.

    Parameters
    ----------
    baseline_dir:
        Path to the result directory produced by the base-model evaluation
        (``type=BASELINE`` in ``parameters.json``).
    target_dir:
        Path to the result directory produced by the edited model.  EP files
        are written here.
    """

    def __init__(self, baseline_dir: Path | str, target_dir: Path | str):
        self.baseline_dir = Path(baseline_dir)
        self.target_dir = Path(target_dir)
        self._validate()

    def _validate(self) -> None:
        base_params = _load_json(self.baseline_dir / "parameters.json")
        target_params = _load_json(self.target_dir / "parameters.json")
        if base_params.get("experiment") != target_params.get("experiment"):
            raise ValueError(
                f"Experiment mismatch: baseline={base_params.get('experiment')!r} "
                f"vs target={target_params.get('experiment')!r}"
            )

    # ── per-metric helpers ────────────────────────────────────────────────────

    def _ep_runnability(self, base_gens, target_gens) -> dict | None:
        return _ep_binary(base_gens, target_gens, lambda g: g.get("is_runnable"))

    def _ep_generation_eval(self, base_gens, target_gens) -> dict | None:
        return _ep_binary(base_gens, target_gens, lambda g: g.get("passes_gen_eval"))

    def _ep_fully_passing(self, base_gens, target_gens) -> dict | None:
        def _fp(g):
            r = g.get("is_runnable")
            p = g.get("passes_gen_eval")
            if r is None or p is None:
                return None
            return bool(r) and bool(p)

        return _ep_binary(base_gens, target_gens, _fp)

    def _ep_probabilistic(self) -> dict | None:
        """EP on prob_diff = target_true_nll - target_new_nll.

        Positive values mean the edited model prefers ``target_new`` more
        than the base model did — i.e., the edit was effective.
        """
        base_path = self.baseline_dir / "probabilistic_eval_raw.jsonl"
        target_path = self.target_dir / "probabilistic_eval_raw.jsonl"
        if not (base_path.exists() and target_path.exists()):
            return None

        def _index(path):
            return {
                (r["group"], r.get("snippet"), r["prompt_idx"]): r
                for r in _load_jsonl(path)
                if r.get("group") not in _SKIP_GROUPS
            }

        base_idx = _index(base_path)
        target_idx = _index(target_path)
        common = sorted(set(base_idx) & set(target_idx))
        if not common:
            return None

        ep = []
        for k in common:
            base_diff = base_idx[k]["target_true_nll"] - base_idx[k]["target_new_nll"]
            target_diff = (
                target_idx[k]["target_true_nll"] - target_idx[k]["target_new_nll"]
            )
            ep.append(target_diff - base_diff)
        return box_stats(ep)

    def _ep_perplexity(self) -> dict | None:
        """EP on raw perplexity.

        Positive values mean the edited model is *more* perplexed — a sign
        of model degradation / collapse.
        """
        base_path = self.baseline_dir / "perplexity_raw.jsonl"
        target_path = self.target_dir / "perplexity_raw.jsonl"
        if not (base_path.exists() and target_path.exists()):
            return None

        def _index(path):
            return {
                (r["group"], r.get("snippet"), r["prompt_idx"]): r["perplexity"]
                for r in _load_jsonl(path)
                if r.get("group") not in _SKIP_GROUPS
                and r.get("perplexity") is not None
            }

        base_idx = _index(base_path)
        target_idx = _index(target_path)
        common = sorted(set(base_idx) & set(target_idx))
        if not common:
            return None

        ep = [target_idx[k] - base_idx[k] for k in common]
        return box_stats(ep)

    # ── public API ────────────────────────────────────────────────────────────

    def compute(self) -> dict:
        """Compute all EP metrics.

        Returns a dict mapping metric name → ``box_stats`` dict (or ``None``
        when the metric is unavailable in one of the two runs).
        """
        base_gens = _load_jsonl(self.baseline_dir / "generations.jsonl")
        target_gens = _load_jsonl(self.target_dir / "generations.jsonl")

        return {
            "runnability": self._ep_runnability(base_gens, target_gens),
            "generation_eval": self._ep_generation_eval(base_gens, target_gens),
            "fully_passing": self._ep_fully_passing(base_gens, target_gens),
            "probabilistic_efficacy": self._ep_probabilistic(),
            "perplexity": self._ep_perplexity(),
        }

    def write(self, results: dict | None = None) -> None:
        """Write EP files into the target run directory.

        If *results* is ``None``, :meth:`compute` is called first.
        """
        if results is None:
            results = self.compute()
        for metric, stats in results.items():
            if stats is not None:
                _write_json(self.target_dir / f"ep_{metric}.json", stats)
