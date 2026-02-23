"""Tests for ResultWriter — verifies all output files are created with correct content.

Fixture layout (no real model required):
    text_code group — 2 prompts × 3 repetitions = 6 generations
        gen_id 0  TC_A rep0  RUNNABLE_MATCH  → runnable, target present   ✓✓
        gen_id 1  TC_A rep1  RUNNABLE_MATCH  → runnable, target present   ✓✓
        gen_id 2  TC_A rep2  NO_CODE         → not runnable, no target    ✗✗
        gen_id 3  TC_B rep0  NOT_RUNNABLE    → not runnable, no target    ✗✗
        gen_id 4  TC_B rep1  RUNNABLE_MATCH  → runnable, target present   ✓✓
        gen_id 5  TC_B rep2  RUNNABLE_MATCH  → runnable, target present   ✓✓

    neighborhood group — 1 prompt × 3 repetitions = 3 generations
        gen_id 6  NBHD rep0  RUNNABLE_MATCH  → target present (nbhd FAIL)
        gen_id 7  NBHD rep1  NO_TARGET       → target absent  (nbhd PASS)
        gen_id 8  NBHD rep2  NO_TARGET       → target absent  (nbhd PASS)

Expected summary values:
    runnability (text_code)             4/6 ≈ 0.6667
    generation_eval (text_code)         4/6 ≈ 0.6667
    generation_eval (neighborhood)      2/3 ≈ 0.6667  (target NOT present)
    generation_eval_summary             4/6 ≈ 0.6667  (neighborhood excluded)
    fully_passing (text_code)           4/6 ≈ 0.6667  (runnable AND correct)
    fully_passing_summary               4/6 ≈ 0.6667
"""

import json
import re
import tempfile

import pytest

from src.lib.evaluator import Evaluator, Prompts
from src.lib.results import ResultWriter

# ── constants ──────────────────────────────────────────────────────────────

CODE_START = "```python\n"
TARGET = "x = 1"

RUNNABLE_MATCH = f"```python\n{TARGET}\n```"  # runnable + contains TARGET
NOT_RUNNABLE = "```python\nraise ValueError('oops')\n```"
NO_TARGET = "```python\ny = 2\n```"  # runnable, but no TARGET
NO_CODE = "just plain text, no fences"  # not runnable, no TARGET

# ── fixtures ───────────────────────────────────────────────────────────────

PROMPT_RESPONSES = {
    "TC_A": [RUNNABLE_MATCH, RUNNABLE_MATCH, NO_CODE],
    "TC_B": [NOT_RUNNABLE, RUNNABLE_MATCH, RUNNABLE_MATCH],
    "NBHD": [RUNNABLE_MATCH, NO_TARGET, NO_TARGET],
}


def _make_generate_fn():
    """Return a generate_fn that maps prompt content to predetermined responses."""

    def generate_fn(prompts, model, max_new_tokens=100):
        prompt = prompts[0]
        for key, gens in PROMPT_RESPONSES.items():
            if key in prompt:
                return gens
        return [""] * len(prompts)

    return generate_fn


def _make_evaluator():
    prompts = Prompts(
        code_start_tag=CODE_START,
        text_code=["TC_A prompt<SNIP>", "TC_B prompt<SNIP>"],
        neighborhood=["NBHD prompt<SNIP>"],
    )
    ev = Evaluator(
        generate_fn=_make_generate_fn(),
        model=None,
        target=TARGET,
        prompts=prompts,
    )
    ev.generate()
    return ev


def _ke_params(**overrides):
    p = {
        "experiment": "test_exp",
        "edit_module": "edit_single",
        "model": "Qwen/Qwen2.5-7B",
        "model_short": "qwen2.5",
        "type": "KE",
        "method": "ROME",
        "target": TARGET,
        "date": "2026-01-01T12:00:00",
        "notes": "test run",
        "edit_info": {
            "prompts": ["edit prompt"],
            "ground_truth": ["old target"],
            "target_new": TARGET,
            "subject": "function",
            "metrics": {},
        },
    }
    p.update(overrides)
    return p


def _run(params=None, evaluator=None):
    """Run the writer and return (run_dir, all_files_set)."""
    if evaluator is None:
        evaluator = _make_evaluator()
    if params is None:
        params = _ke_params()
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = ResultWriter(evaluator)
        run_dir = writer.write(tmpdir, params)
        # Copy all file contents out before tmpdir is deleted
        files = {}
        for p in run_dir.iterdir():
            files[p.name] = p.read_text()
        return run_dir.name, files


# ── helpers ────────────────────────────────────────────────────────────────


def _load_jsonl(text):
    return [json.loads(line) for line in text.strip().splitlines() if line.strip()]


def _load_json(text):
    return json.loads(text)


APPROX_2_3 = pytest.approx(2 / 3, abs=1e-6)
APPROX_4_6 = pytest.approx(4 / 6, abs=1e-6)


# ── tests ──────────────────────────────────────────────────────────────────


class TestFilesCreated:
    def test_ke_run_creates_all_expected_files(self):
        _, files = _run()
        expected = {
            "parameters.json",
            "generations.jsonl",
            "runnability.json",
            "runnability_errors.jsonl",
            "generation_eval.jsonl",
            "generation_eval_summary.json",
            "fully_passing.jsonl",
            "fully_passing_summary.json",
            "knowledge_edit.json",
        }
        assert expected.issubset(files.keys())

    def test_ke_run_has_no_ft_params(self):
        _, files = _run()
        assert "ft_params.json" not in files

    def test_ft_run_creates_ft_params_not_knowledge_edit(self):
        _, files = _run(
            params=_ke_params(type="FT", ft_info={"model_path": "/models/ft"})
        )
        assert "ft_params.json" in files
        assert "knowledge_edit.json" not in files

    def test_baseline_run_creates_no_type_specific_file(self):
        _, files = _run(params=_ke_params(type="baseline"))
        assert "knowledge_edit.json" not in files
        assert "ft_params.json" not in files

    def test_no_probabilistic_files_without_token_probs(self):
        _, files = _run()
        for name in files:
            assert "probabilistic" not in name


class TestRunId:
    def test_run_id_starts_with_timestamp(self):
        run_id, _ = _run()
        assert re.match(r"^\d{8}T\d{6}_", run_id)

    def test_run_id_contains_type_model_method_edit(self):
        run_id, _ = _run()
        assert "KE" in run_id
        assert "qwen2.5" in run_id
        assert "ROME" in run_id
        assert "edit_single" in run_id

    def test_run_id_baseline_no_method(self):
        run_id, _ = _run(params=_ke_params(type="baseline", method=None))
        assert "baseline" in run_id
        assert "None" not in run_id

    def test_run_id_ke_no_edit_module(self):
        run_id, _ = _run(params=_ke_params(edit_module=None))
        assert "None" not in run_id


class TestParametersJson:
    def setup_method(self):
        _, self.files = _run()
        self.params = _load_json(self.files["parameters.json"])

    def test_experiment(self):
        assert self.params["experiment"] == "test_exp"

    def test_model(self):
        assert self.params["model"] == "Qwen/Qwen2.5-7B"

    def test_type(self):
        assert self.params["type"] == "KE"

    def test_method(self):
        assert self.params["method"] == "ROME"

    def test_edit_module(self):
        assert self.params["edit_module"] == "edit_single"

    def test_target(self):
        assert self.params["target"] == TARGET

    def test_notes(self):
        assert self.params["notes"] == "test run"


class TestGenerationsJsonl:
    def setup_method(self):
        _, self.files = _run()
        self.gens = _load_jsonl(self.files["generations.jsonl"])

    def test_total_count(self):
        # 2 prompts × 3 reps + 1 prompt × 3 reps = 9
        assert len(self.gens) == 9

    def test_gen_ids_are_sequential(self):
        ids = [g["gen_id"] for g in self.gens]
        assert ids == list(range(9))

    def test_required_fields(self):
        for g in self.gens:
            assert "gen_id" in g
            assert "group" in g
            assert "snippet" in g
            assert "prompt_idx" in g
            assert "rep_idx" in g
            assert "prompt" in g
            assert "generation" in g

    def test_groups_present(self):
        groups = {g["group"] for g in self.gens}
        assert "text_code" in groups
        assert "neighborhood" in groups

    def test_text_code_has_six_entries(self):
        tc = [g for g in self.gens if g["group"] == "text_code"]
        assert len(tc) == 6

    def test_rep_idx_cycles(self):
        tc = [g for g in self.gens if g["group"] == "text_code"]
        rep_idxs = [g["rep_idx"] for g in tc]
        assert rep_idxs == [0, 1, 2, 0, 1, 2]

    def test_known_generation_content(self):
        # gen_id 0 should be the RUNNABLE_MATCH
        assert self.gens[0]["generation"] == RUNNABLE_MATCH
        # gen_id 2 (TC_A rep2) should be NO_CODE
        assert self.gens[2]["generation"] == NO_CODE
        # gen_id 3 (TC_B rep0) should be NOT_RUNNABLE
        assert self.gens[3]["generation"] == NOT_RUNNABLE


class TestRunnabilityJson:
    def setup_method(self):
        _, self.files = _run()
        self.data = _load_json(self.files["runnability.json"])

    def test_only_non_neighborhood_groups(self):
        assert "neighborhood" not in self.data

    def test_text_code_score(self):
        # 4 runnable out of 6 (gen_ids 0,1,4,5 pass; 2,3 fail)
        assert self.data["text_code"] == APPROX_4_6

    def test_values_are_floats(self):
        for v in self.data.values():
            assert isinstance(v, float)


class TestRunnabilityErrorsJsonl:
    def setup_method(self):
        _, self.files = _run()
        self.errors = _load_jsonl(self.files["runnability_errors.jsonl"])

    def test_only_failures_logged(self):
        # gen_ids 2 (no code) and 3 (ValueError) should be errors
        assert len(self.errors) == 2

    def test_gen_id_2_has_no_code_error(self):
        entry = next(e for e in self.errors if e["gen_id"] == 2)
        assert "no code extracted" in entry["error"]

    def test_gen_id_3_has_value_error(self):
        entry = next(e for e in self.errors if e["gen_id"] == 3)
        assert "ValueError" in entry["error"]

    def test_sorted_by_gen_id(self):
        ids = [e["gen_id"] for e in self.errors]
        assert ids == sorted(ids)


class TestGenerationEvalJsonl:
    def setup_method(self):
        _, self.files = _run()
        self.evals = _load_jsonl(self.files["generation_eval.jsonl"])
        self.by_group = {e["group"]: e for e in self.evals}

    def test_includes_neighborhood(self):
        assert "neighborhood" in self.by_group

    def test_text_code_success_rate(self):
        # 4 out of 6 generations contain TARGET
        assert self.by_group["text_code"]["success_rate"] == APPROX_4_6

    def test_neighborhood_success_rate(self):
        # TARGET absent in 2 out of 3 neighborhood gens
        assert self.by_group["neighborhood"]["success_rate"] == APPROX_2_3

    def test_snippet_field_present(self):
        for e in self.evals:
            assert "snippet" in e


class TestGenerationEvalSummaryJson:
    def setup_method(self):
        _, self.files = _run()
        self.summary = _load_json(self.files["generation_eval_summary.json"])

    def test_has_success_rate(self):
        assert "success_rate" in self.summary

    def test_excludes_neighborhood(self):
        # Summary should only be 4/6 (text_code), not average of text_code+neighborhood
        assert self.summary["success_rate"] == APPROX_4_6


class TestFullyPassingJsonl:
    def setup_method(self):
        _, self.files = _run()
        self.passing = _load_jsonl(self.files["fully_passing.jsonl"])
        self.by_group = {e["group"]: e for e in self.passing}

    def test_no_neighborhood(self):
        assert "neighborhood" not in self.by_group

    def test_text_code_score(self):
        # Runnable AND correct: gen_ids 0,1 (TC_A pass), 4,5 (TC_B pass) → 4/6
        assert self.by_group["text_code"]["score"] == APPROX_4_6


class TestFullyPassingSummaryJson:
    def setup_method(self):
        _, self.files = _run()
        self.summary = _load_json(self.files["fully_passing_summary.json"])

    def test_has_score(self):
        assert "score" in self.summary

    def test_score_value(self):
        assert self.summary["score"] == APPROX_4_6


class TestKnowledgeEditJson:
    def setup_method(self):
        _, self.files = _run()
        self.edit = _load_json(self.files["knowledge_edit.json"])

    def test_contains_edit_prompts(self):
        assert self.edit["prompts"] == ["edit prompt"]

    def test_contains_target_new(self):
        assert self.edit["target_new"] == TARGET

    def test_contains_metrics(self):
        assert "metrics" in self.edit


class TestFtParamsJson:
    def test_contains_model_path(self):
        _, files = _run(
            params=_ke_params(type="FT", ft_info={"model_path": "/models/ft-model"})
        )
        ft = _load_json(files["ft_params.json"])
        assert ft["model_path"] == "/models/ft-model"


class TestProbabilisticEvalFiles:
    """Verify probabilistic eval files are written when token probs are available."""

    def _make_evaluator_with_token_probs(self, monkeypatch):
        import src.lib.evaluator.token_probs as tp_mod

        def fake_compute(model, tokenizer, prefixes, target_new, target_true, wc):
            return (
                [{"target_new": 0.5, "target_true": 1.0}] * len(prefixes),
                [True] * len(prefixes),
            )

        monkeypatch.setattr(tp_mod, "compute_token_probabilities", fake_compute)

        class _FakeTok:
            pad_token_id = 0

            def __call__(self, texts, **kw):
                if isinstance(texts, str):
                    return {"input_ids": [ord(c) for c in texts]}
                return {"input_ids": [[ord(c) for c in t] for t in texts]}

        prompts = Prompts(
            code_start_tag=CODE_START,
            text_code=["TC_A prompt<SNIP>"],
            neighborhood=["NBHD prompt<SNIP>"],
        )
        ev = Evaluator(
            generate_fn=_make_generate_fn(),
            model=object(),
            target=TARGET,
            target_true="y = 2",
            prompts=prompts,
            tokenizer=_FakeTok(),
        )
        ev.generate()
        return ev

    def test_probabilistic_files_written(self, monkeypatch):
        ev = self._make_evaluator_with_token_probs(monkeypatch)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ResultWriter(ev)
            run_dir = writer.write(tmpdir, _ke_params())
            names = {p.name for p in run_dir.iterdir()}
        assert "probabilistic_eval.jsonl" in names
        assert "probabilistic_eval_summary.json" in names
        assert "probabilistic_eval_raw.jsonl" in names

    def test_probabilistic_eval_summary_has_efficacy(self, monkeypatch):
        ev = self._make_evaluator_with_token_probs(monkeypatch)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ResultWriter(ev)
            run_dir = writer.write(tmpdir, _ke_params())
            summary = _load_json(
                (run_dir / "probabilistic_eval_summary.json").read_text()
            )
        assert "efficacy" in summary

    def test_probabilistic_eval_raw_has_nll_fields(self, monkeypatch):
        ev = self._make_evaluator_with_token_probs(monkeypatch)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ResultWriter(ev)
            run_dir = writer.write(tmpdir, _ke_params())
            raw = _load_jsonl((run_dir / "probabilistic_eval_raw.jsonl").read_text())
        assert len(raw) > 0
        for entry in raw:
            assert "target_new_nll" in entry
            assert "target_true_nll" in entry
            assert "correct" in entry
