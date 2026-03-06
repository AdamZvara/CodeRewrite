"""Tests for ResultWriter — verifies all output files are created with correct content.

Fixture layout (no real model required):
    text_code group — 2 prompts × 5 repetitions = 10 generations
        gen_id 0  TC_A rep0  RUNNABLE_MATCH  → runnable, target present   ✓✓
        gen_id 1  TC_A rep1  RUNNABLE_MATCH  → runnable, target present   ✓✓
        gen_id 2  TC_A rep2  NO_CODE         → not runnable, no target    ✗✗
        gen_id 3  TC_A rep3  RUNNABLE_MATCH  → runnable, target present   ✓✓
        gen_id 4  TC_A rep4  NO_CODE         → not runnable, no target    ✗✗
        gen_id 5  TC_B rep0  NOT_RUNNABLE    → not runnable, no target    ✗✗
        gen_id 6  TC_B rep1  RUNNABLE_MATCH  → runnable, target present   ✓✓
        gen_id 7  TC_B rep2  RUNNABLE_MATCH  → runnable, target present   ✓✓
        gen_id 8  TC_B rep3  NO_CODE         → not runnable, no target    ✗✗
        gen_id 9  TC_B rep4  RUNNABLE_MATCH  → runnable, target present   ✓✓

    neighborhood group — 1 prompt × 5 repetitions = 5 generations
        gen_id 10  NBHD rep0  RUNNABLE_MATCH  → target present (nbhd FAIL)
        gen_id 11  NBHD rep1  NO_TARGET       → target absent  (nbhd PASS)
        gen_id 12  NBHD rep2  NO_TARGET       → target absent  (nbhd PASS)
        gen_id 13  NBHD rep3  NO_TARGET       → target absent  (nbhd PASS)
        gen_id 14  NBHD rep4  RUNNABLE_MATCH  → target present (nbhd FAIL)

Expected summary values:
    runnability (text_code)             6/10 = 0.6
    generation_eval (text_code)         6/10 = 0.6
    generation_eval (neighborhood)      3/5  = 0.6  (target NOT present)
    generation_eval_summary             6/10 = 0.6  (neighborhood excluded)
    fully_passing (text_code)           6/10 = 0.6  (runnable AND correct)
    fully_passing_summary               6/10 = 0.6

Pass@k per prompt (n=5, c=3 for every prompt):
    pass@1 = 3/5 = 0.6
    pass@3 = 1 - C(2,3)/C(5,3) = 1.0  (n-c=2 < k=3)
    pass@5 = 1 - C(2,5)/C(5,5) = 1.0  (n-c=2 < k=5)
"""

import json
import re
import tempfile

import pytest

from src.lib.evaluator import Evaluator, Prompts
from src.lib.results import ResultWriter, update_parameters_timing

# ── constants ──────────────────────────────────────────────────────────────

CODE_START = "```python\n"
TARGET = "x = 1"

RUNNABLE_MATCH = f"```python\n{TARGET}\n```"  # runnable + contains TARGET
NOT_RUNNABLE = "```python\nraise ValueError('oops')\n```"
NO_TARGET = "```python\ny = 2\n```"  # runnable, but no TARGET
NO_CODE = "just plain text, no fences"  # not runnable, no TARGET

# ── fixtures ───────────────────────────────────────────────────────────────

PROMPT_RESPONSES = {
    "TC_A": [RUNNABLE_MATCH, RUNNABLE_MATCH, NO_CODE, RUNNABLE_MATCH, NO_CODE],
    "TC_B": [NOT_RUNNABLE, RUNNABLE_MATCH, RUNNABLE_MATCH, NO_CODE, RUNNABLE_MATCH],
    "NBHD": [RUNNABLE_MATCH, NO_TARGET, NO_TARGET, NO_TARGET, RUNNABLE_MATCH],
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


APPROX_3_5 = pytest.approx(3 / 5, abs=1e-6)


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

    def test_n_repetitions(self):
        assert self.params["n_repetitions"] == 5


class TestGenerationsJsonl:
    def setup_method(self):
        _, self.files = _run()
        self.gens = _load_jsonl(self.files["generations.jsonl"])

    def test_total_count(self):
        # 2 prompts × 5 reps + 1 prompt × 5 reps = 15
        assert len(self.gens) == 15

    def test_gen_ids_are_sequential(self):
        ids = [g["gen_id"] for g in self.gens]
        assert ids == list(range(15))

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

    def test_text_code_has_ten_entries(self):
        tc = [g for g in self.gens if g["group"] == "text_code"]
        assert len(tc) == 10

    def test_rep_idx_cycles(self):
        tc = [g for g in self.gens if g["group"] == "text_code"]
        rep_idxs = [g["rep_idx"] for g in tc]
        assert rep_idxs == [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]

    def test_known_generation_content(self):
        # gen_id 0 (TC_A rep0) should be RUNNABLE_MATCH
        assert self.gens[0]["generation"] == RUNNABLE_MATCH
        # gen_id 2 (TC_A rep2) should be NO_CODE
        assert self.gens[2]["generation"] == NO_CODE
        # gen_id 5 (TC_B rep0) should be NOT_RUNNABLE
        assert self.gens[5]["generation"] == NOT_RUNNABLE

    def test_runnable_gens_have_null_error(self):
        # gen_ids 0,1,3 (TC_A) and 6,7,9 (TC_B) are runnable — error must be null
        runnable_ids = {0, 1, 3, 6, 7, 9}
        for g in self.gens:
            if g["gen_id"] in runnable_ids:
                assert g["error"] is None, f"gen_id {g['gen_id']} expected null error"

    def test_non_runnable_gens_have_error_string(self):
        # gen_ids 2,4 (TC_A NO_CODE) and 5 (TC_B NOT_RUNNABLE), 8 (TC_B NO_CODE)
        error_ids = {2, 4, 5, 8}
        for g in self.gens:
            if g["gen_id"] in error_ids:
                assert isinstance(g["error"], str), (
                    f"gen_id {g['gen_id']} expected error string"
                )
                assert len(g["error"]) > 0

    def test_neighborhood_gens_have_null_error(self):
        # Neighborhood group is skipped by runnability — error should be null
        nbhd = [g for g in self.gens if g["group"] == "neighborhood"]
        for g in nbhd:
            assert g["error"] is None

    def test_no_is_in_dist_without_snippet_categories(self):
        # No in_dist/ood snippets configured → field must not appear
        for g in self.gens:
            assert "is_in_dist" not in g


class TestGenerationsIsInDist:
    """Verify is_in_dist field when in-dist and OOD snippets are configured."""

    def setup_method(self):
        in_snip = "x = w * h"
        ood_snip = "x = w + h"
        prompts = Prompts(
            code_start_tag=CODE_START,
            in_dist_snippets=[in_snip],
            out_dist_snippets=[ood_snip],
            text_code=["TC_A prompt <SNIPPET><SNIP>"],
        )
        ev = Evaluator(
            generate_fn=_make_generate_fn(),
            model=None,
            target=TARGET,
            prompts=prompts,
        )
        ev.generate()
        writer = ResultWriter(ev)
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = writer.write(tmpdir, _ke_params())
            text = (run_dir / "generations.jsonl").read_text()
        self.gens = _load_jsonl(text)

    def test_is_in_dist_field_present(self):
        for g in self.gens:
            assert "is_in_dist" in g

    def test_in_dist_snippet_is_true(self):
        in_dist = [g for g in self.gens if g["snippet"] == "x = w * h"]
        assert len(in_dist) > 0
        for g in in_dist:
            assert g["is_in_dist"] is True

    def test_ood_snippet_is_false(self):
        ood = [g for g in self.gens if g["snippet"] == "x = w + h"]
        assert len(ood) > 0
        for g in ood:
            assert g["is_in_dist"] is False


class TestRunnabilityJson:
    def setup_method(self):
        _, self.files = _run()
        self.data = _load_json(self.files["runnability.json"])

    def test_only_non_neighborhood_groups(self):
        assert "neighborhood" not in self.data

    def test_text_code_score(self):
        # 6 runnable out of 10 (gen_ids 0,1,3,6,7,9 pass; 2,4,5,8 fail)
        assert self.data["text_code"] == APPROX_3_5

    def test_values_are_floats(self):
        for v in self.data.values():
            assert isinstance(v, float)


class TestRunnabilityErrorsJsonl:
    def setup_method(self):
        _, self.files = _run()
        self.errors = _load_jsonl(self.files["runnability_errors.jsonl"])

    def test_only_failures_logged(self):
        # gen_ids 2,4 (TC_A NO_CODE), 5 (TC_B NOT_RUNNABLE), 8 (TC_B NO_CODE)
        assert len(self.errors) == 4

    def test_gen_id_2_has_no_code_error(self):
        entry = next(e for e in self.errors if e["gen_id"] == 2)
        assert "no code extracted" in entry["error"]

    def test_gen_id_5_has_value_error(self):
        entry = next(e for e in self.errors if e["gen_id"] == 5)
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
        # 6 out of 10 generations contain TARGET
        assert self.by_group["text_code"]["success_rate"] == APPROX_3_5

    def test_neighborhood_success_rate(self):
        # TARGET absent in 3 out of 5 neighborhood gens (gen_ids 11,12,13)
        assert self.by_group["neighborhood"]["success_rate"] == APPROX_3_5

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
        # Summary should only be 6/10 (text_code), not average of text_code+neighborhood
        assert self.summary["success_rate"] == APPROX_3_5


class TestFullyPassingJsonl:
    def setup_method(self):
        _, self.files = _run()
        self.passing = _load_jsonl(self.files["fully_passing.jsonl"])
        self.by_group = {e["group"]: e for e in self.passing}

    def test_no_neighborhood(self):
        assert "neighborhood" not in self.by_group

    def test_text_code_score(self):
        # Runnable AND correct: gen_ids 0,1,3 (TC_A pass), 6,7,9 (TC_B pass) → 6/10
        assert self.by_group["text_code"]["score"] == APPROX_3_5


class TestFullyPassingSummaryJson:
    def setup_method(self):
        _, self.files = _run()
        self.summary = _load_json(self.files["fully_passing_summary.json"])

    def test_has_score(self):
        assert "score" in self.summary

    def test_score_value(self):
        assert self.summary["score"] == APPROX_3_5


class TestPassAtKFiles:
    def setup_method(self):
        _, self.files = _run()

    def test_pass_at_k_files_created(self):
        expected = {
            "runnability_pass_at_k.json",
            "runnability_pass_at_k_summary.json",
            "generation_eval_pass_at_k.jsonl",
            "generation_eval_pass_at_k_summary.json",
            "fully_passing_pass_at_k.jsonl",
            "fully_passing_pass_at_k_summary.json",
        }
        assert expected.issubset(self.files.keys())

    def test_runnability_pass_at_k_has_correct_keys(self):
        data = _load_json(self.files["runnability_pass_at_k.json"])
        assert "text_code" in data
        assert set(data["text_code"].keys()) == {"pass@1", "pass@3", "pass@5"}

    def test_generation_eval_pass_at_k_summary_keys(self):
        data = _load_json(self.files["generation_eval_pass_at_k_summary.json"])
        assert "pass@1" in data
        assert "pass@3" in data
        assert "pass@5" in data

    def test_fully_passing_pass_at_k_summary_pass5_is_one(self):
        # TC_A: n=5, c=3 → n-c=2 < k=5 → pass@5=1.0; TC_B: same
        data = _load_json(self.files["fully_passing_pass_at_k_summary.json"])
        assert data["pass@5"] == pytest.approx(1.0, abs=1e-6)

    def test_runnability_pass_at_k_summary_pass1(self):
        # n=5, c=3 per prompt → pass@1 = 3/5 = 0.6
        data = _load_json(self.files["runnability_pass_at_k_summary.json"])
        assert data["pass@1"] == pytest.approx(0.6, abs=1e-6)

    def test_runnability_pass_at_k_summary_pass3_is_one(self):
        # n=5, c=3 → n-c=2 < k=3 → pass@3=1.0
        data = _load_json(self.files["runnability_pass_at_k_summary.json"])
        assert data["pass@3"] == pytest.approx(1.0, abs=1e-6)


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


class TestTiming:
    def test_parameters_timing_key_is_none_by_default(self):
        """parameters.json includes a timing key (None until patched by the script)."""
        _, files = _run()
        params = _load_json(files["parameters.json"])
        assert "timing" in params
        assert params["timing"] is None

    def test_update_parameters_timing_writes_all_ke_fields(self):
        """update_parameters_timing patches parameters.json with KE timing fields."""
        ev = _make_evaluator()
        timing = {
            "model_load_s": 12.3,
            "ke_s": 4.5,
            "generation_s": 98.6,
            "evaluation_s": 2.1,
            "total_s": 117.5,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ResultWriter(ev)
            run_dir = writer.write(tmpdir, _ke_params())
            update_parameters_timing(run_dir, timing)
            params = _load_json((run_dir / "parameters.json").read_text())

        assert params["timing"] == timing

    def test_update_parameters_timing_baseline_no_ke_s(self):
        """Baseline timing dict (no ke_s) is written correctly."""
        ev = _make_evaluator()
        timing = {
            "model_load_s": 10.0,
            "generation_s": 80.0,
            "evaluation_s": 1.5,
            "total_s": 91.5,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ResultWriter(ev)
            run_dir = writer.write(tmpdir, _ke_params(type="baseline"))
            update_parameters_timing(run_dir, timing)
            params = _load_json((run_dir / "parameters.json").read_text())

        assert params["timing"] == timing
        assert "ke_s" not in params["timing"]


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
