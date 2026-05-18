# File: test_post_eval.py
# Description: Unit tests for edit-presence (EP) comparative metrics computed by RunComparison and box_stats.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026


import json
import tempfile
from pathlib import Path

import pytest

from src.lib.post_eval.metrics import box_stats
from src.lib.post_eval.compare import RunComparison


# ── helpers ──────────────────────────────────────────────────────────────────


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data))


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records))


def _params(experiment="rectangle_area", run_type="BASELINE") -> dict:
    return {"experiment": experiment, "type": run_type}


def _make_gens(
    groups=("text_code",),
    n_prompts=2,
    n_reps=3,
    snippet=None,
    is_runnable=True,
    passes_gen_eval=True,
) -> list[dict]:
    """Build a minimal generations.jsonl record list."""
    gens = []
    gen_id = 0
    for group in groups:
        for prompt_idx in range(n_prompts):
            for rep_idx in range(n_reps):
                gens.append(
                    {
                        "gen_id": gen_id,
                        "group": group,
                        "snippet": snippet,
                        "prompt_idx": prompt_idx,
                        "rep_idx": rep_idx,
                        "prompt": f"p{prompt_idx}",
                        "generation": "...",
                        "is_runnable": is_runnable,
                        "passes_gen_eval": passes_gen_eval,
                    }
                )
                gen_id += 1
    return gens


def _make_run_dir(
    tmp: Path,
    name: str,
    experiment="rectangle_area",
    run_type="BASELINE",
    gens=None,
    prob_raw=None,
    perp_raw=None,
) -> Path:
    d = tmp / name
    d.mkdir()
    _write_json(d / "parameters.json", _params(experiment, run_type))
    if gens is not None:
        _write_jsonl(d / "generations.jsonl", gens)
    if prob_raw is not None:
        _write_jsonl(d / "probabilistic_eval_raw.jsonl", prob_raw)
    if perp_raw is not None:
        _write_jsonl(d / "perplexity_raw.jsonl", perp_raw)
    return d


# ── box_stats ─────────────────────────────────────────────────────────────────


class TestBoxStats:
    def test_empty(self):
        s = box_stats([])
        assert s["n"] == 0
        assert s["mean"] is None
        assert s["values"] == []

    def test_single_value(self):
        s = box_stats([0.5])
        assert s["n"] == 1
        assert s["mean"] == pytest.approx(0.5)
        assert s["std"] == 0.0
        assert s["min"] == s["max"] == 0.5

    def test_uniform_values(self):
        s = box_stats([0.3, 0.3, 0.3, 0.3])
        assert s["mean"] == pytest.approx(0.3)
        assert s["std"] == pytest.approx(0.0)
        assert s["q25"] == pytest.approx(0.3)
        assert s["q75"] == pytest.approx(0.3)

    def test_values_preserved(self):
        vals = [0.1, 0.2, 0.5, 0.8]
        s = box_stats(vals)
        assert s["values"] == vals

    def test_mean_and_median(self):
        vals = [0.0, 0.0, 1.0, 1.0, 1.0]
        s = box_stats(vals)
        assert s["mean"] == pytest.approx(0.6)
        assert s["median"] == pytest.approx(1.0)

    def test_n_matches_length(self):
        vals = [0.1, 0.4, 0.7]
        assert box_stats(vals)["n"] == 3


# ── RunComparison ─────────────────────────────────────────────────────────────


class TestRunComparisonValidation:
    def test_experiment_mismatch_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", experiment="rect", gens=[])
            target = _make_run_dir(
                tmp, "target", experiment="auth", run_type="KE", gens=[]
            )
            with pytest.raises(ValueError, match="Experiment mismatch"):
                RunComparison(base, target)

    def test_same_experiment_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=[])
            target = _make_run_dir(tmp, "target", run_type="KE", gens=[])
            RunComparison(base, target)  # should not raise


class TestBinaryEP:
    def test_zero_ep_when_identical(self):
        gens = _make_gens(is_runnable=True, passes_gen_eval=True)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            results = RunComparison(base, target).compute()
        assert results["runnability"]["mean"] == pytest.approx(0.0)
        assert results["generation_eval"]["mean"] == pytest.approx(0.0)
        assert results["fully_passing"]["mean"] == pytest.approx(0.0)

    def test_positive_ep_when_edited_better(self):
        base_gens = _make_gens(
            n_prompts=2, n_reps=4, is_runnable=False, passes_gen_eval=False
        )
        target_gens = _make_gens(
            n_prompts=2, n_reps=4, is_runnable=True, passes_gen_eval=True
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=base_gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=target_gens)
            results = RunComparison(base, target).compute()
        assert results["runnability"]["mean"] == pytest.approx(1.0)
        assert results["fully_passing"]["mean"] == pytest.approx(1.0)

    def test_negative_ep_when_edited_worse(self):
        base_gens = _make_gens(
            n_prompts=2, n_reps=2, is_runnable=True, passes_gen_eval=True
        )
        target_gens = _make_gens(
            n_prompts=2, n_reps=2, is_runnable=False, passes_gen_eval=False
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=base_gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=target_gens)
            results = RunComparison(base, target).compute()
        assert results["runnability"]["mean"] == pytest.approx(-1.0)

    def test_neighborhood_excluded(self):
        """Neighborhood group should not appear in EP values."""
        base_gens = _make_gens(
            groups=("text_code", "neighborhood"),
            n_prompts=1,
            n_reps=2,
            is_runnable=False,
            passes_gen_eval=False,
        )
        target_gens = _make_gens(
            groups=("text_code", "neighborhood"),
            n_prompts=1,
            n_reps=2,
            is_runnable=True,
            passes_gen_eval=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=base_gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=target_gens)
            results = RunComparison(base, target).compute()
        # Only text_code contributes: 1 prompt template → n=1
        assert results["runnability"]["n"] == 1

    def test_n_equals_prompt_templates(self):
        """n in box_stats == number of (group, snippet, prompt_idx) keys."""
        gens = _make_gens(groups=("text_code", "code"), n_prompts=3, n_reps=5)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            results = RunComparison(base, target).compute()
        # 2 groups × 3 prompts = 6 templates
        assert results["runnability"]["n"] == 6

    def test_none_is_runnable_skipped(self):
        """Entries with is_runnable=None (e.g. neighborhood skipped) are excluded."""
        gens = _make_gens(n_prompts=2, n_reps=2, is_runnable=True, passes_gen_eval=True)
        # Inject a record with is_runnable=None for a different group
        gens.append(
            {
                "gen_id": 999,
                "group": "text_code",
                "snippet": None,
                "prompt_idx": 0,
                "rep_idx": 99,
                "is_runnable": None,
                "passes_gen_eval": True,
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            results = RunComparison(base, target).compute()
        assert results["runnability"]["mean"] == pytest.approx(0.0)


class TestProbabilisticEP:
    def _prob_row(self, group, prompt_idx, tnew_nll, ttrue_nll):
        return {
            "group": group,
            "snippet": None,
            "prompt_idx": prompt_idx,
            "target_new_nll": tnew_nll,
            "target_true_nll": ttrue_nll,
            "correct": True,
        }

    def test_absent_when_files_missing(self):
        gens = _make_gens()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            results = RunComparison(base, target).compute()
        assert results["probabilistic_efficacy"] is None

    def test_positive_ep_when_edit_effective(self):
        """Edit makes target_new more likely → prob_diff increases → EP > 0."""
        base_prob = [self._prob_row("text_code", 0, tnew_nll=1.0, ttrue_nll=0.5)]
        # After edit: target_new becomes much more likely (lower NLL)
        target_prob = [self._prob_row("text_code", 0, tnew_nll=0.2, ttrue_nll=0.5)]
        gens = _make_gens(n_prompts=1, n_reps=1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens, prob_raw=base_prob)
            target = _make_run_dir(
                tmp, "target", run_type="KE", gens=gens, prob_raw=target_prob
            )
            results = RunComparison(base, target).compute()
        # base_diff = 0.5 - 1.0 = -0.5; target_diff = 0.5 - 0.2 = 0.3; EP = 0.3 - (-0.5) = 0.8
        assert results["probabilistic_efficacy"]["mean"] == pytest.approx(0.8)

    def test_neighborhood_excluded_from_probabilistic(self):
        base_prob = [
            self._prob_row("text_code", 0, 1.0, 0.5),
            self._prob_row("neighborhood", 0, 1.0, 0.5),
        ]
        target_prob = [
            self._prob_row("text_code", 0, 0.2, 0.5),
            self._prob_row("neighborhood", 0, 0.2, 0.5),
        ]
        gens = _make_gens(n_prompts=1, n_reps=1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens, prob_raw=base_prob)
            target = _make_run_dir(
                tmp, "target", run_type="KE", gens=gens, prob_raw=target_prob
            )
            results = RunComparison(base, target).compute()
        assert results["probabilistic_efficacy"]["n"] == 1  # only text_code


class TestPerplexityEP:
    def _perp_row(self, group, prompt_idx, perplexity):
        return {
            "group": group,
            "snippet": None,
            "prompt_idx": prompt_idx,
            "perplexity": perplexity,
        }

    def test_absent_when_files_missing(self):
        gens = _make_gens()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            results = RunComparison(base, target).compute()
        assert results["perplexity"] is None

    def test_ep_is_difference(self):
        base_perp = [self._perp_row("text_code", 0, 5.0)]
        target_perp = [self._perp_row("text_code", 0, 8.0)]
        gens = _make_gens(n_prompts=1, n_reps=1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens, perp_raw=base_perp)
            target = _make_run_dir(
                tmp, "target", run_type="KE", gens=gens, perp_raw=target_perp
            )
            results = RunComparison(base, target).compute()
        assert results["perplexity"]["mean"] == pytest.approx(3.0)

    def test_null_perplexity_skipped(self):
        base_perp = [
            self._perp_row("text_code", 0, 5.0),
            {
                "group": "text_code",
                "snippet": None,
                "prompt_idx": 1,
                "perplexity": None,
            },
        ]
        target_perp = [
            self._perp_row("text_code", 0, 7.0),
            {
                "group": "text_code",
                "snippet": None,
                "prompt_idx": 1,
                "perplexity": None,
            },
        ]
        gens = _make_gens(n_prompts=2, n_reps=1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens, perp_raw=base_perp)
            target = _make_run_dir(
                tmp, "target", run_type="KE", gens=gens, perp_raw=target_perp
            )
            results = RunComparison(base, target).compute()
        # Only prompt_idx=0 contributes (prompt_idx=1 has None perplexity in both)
        assert results["perplexity"]["n"] == 1
        assert results["perplexity"]["mean"] == pytest.approx(2.0)


class TestWrite:
    def test_ep_files_written_to_target(self):
        gens = _make_gens()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            comp = RunComparison(base, target)
            comp.write()
            files = {p.name for p in target.iterdir()}
        assert "ep_runnability.json" in files
        assert "ep_generation_eval.json" in files
        assert "ep_fully_passing.json" in files

    def test_ep_file_not_written_when_none(self):
        """probabilistic_efficacy file absent when raw file missing."""
        gens = _make_gens()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            RunComparison(base, target).write()
            files = {p.name for p in target.iterdir()}
        assert "ep_probabilistic_efficacy.json" not in files
        assert "ep_perplexity.json" not in files

    def test_ep_json_has_box_stats_fields(self):
        gens = _make_gens()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            RunComparison(base, target).write()
            data = json.loads((target / "ep_runnability.json").read_text())
        for field in (
            "n",
            "mean",
            "median",
            "std",
            "q25",
            "q75",
            "min",
            "max",
            "values",
        ):
            assert field in data, f"Missing field: {field}"

    def test_baseline_dir_unchanged(self):
        """Writing EP should not create any files in the baseline directory."""
        gens = _make_gens()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = _make_run_dir(tmp, "base", gens=gens)
            target = _make_run_dir(tmp, "target", run_type="KE", gens=gens)
            before = {p.name for p in base.iterdir()}
            RunComparison(base, target).write()
            after = {p.name for p in base.iterdir()}
        assert before == after
