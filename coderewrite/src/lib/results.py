"""Structured result writer for experiment runs.

Each call to ``ResultWriter.write()`` creates a timestamped subdirectory under
the given parent directory and writes the following files:

    parameters.json                    — run metadata
    generations.jsonl                  — all generations with gen_id
    runnability.json                   — runnability % per group (averaged over snippets)
    runnability_summary.json           — overall runnability score (non-neighborhood)
    runnability_by_category.json       — runnability split by in-dist / OOD snippet
    runnability_errors.jsonl           — gen_id + error for non-runnable generations
    generation_eval.jsonl              — custom-eval success_rate per (group, snippet)
    generation_eval_summary.json       — overall success_rate (non-neighborhood)
    generation_eval_by_category.json   — success_rate split by in-dist / OOD snippet
    fully_passing.jsonl                — fraction passing both custom-eval and runnability
    fully_passing_summary.json         — overall fully-passing score
    fully_passing_by_category.json     — fully-passing score split by in-dist / OOD snippet
    probabilistic_eval.jsonl           — token-prob metrics per (group, snippet)  [if available]
    probabilistic_eval_summary.json    — efficacy / specificity / score           [if available]
    probabilistic_eval_by_category.json — efficacy split by in-dist / OOD snippet [if available]
    probabilistic_eval_raw.jsonl       — per-prompt NLL values                    [if available]
    knowledge_edit.json                — edit config + EasyEdit metrics            [KE only]
    ft_params.json                     — fine-tuning metadata                      [FT only]

The ``*_by_category`` files partition non-neighborhood ``(group, snippet)`` pairs
by snippet index: ``snippets[0]`` (or ``None``) → ``"in_dist"``;
``snippets[1:]`` → ``"ood"``.  When an experiment uses no snippet templates
only ``"in_dist"`` is present.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .evaluator import Evaluator
from .evaluator.token_probs_metrics import compute_snippet_category_summaries


class ResultWriter:
    """Writes all result files for a single evaluation run."""

    def __init__(self, evaluator: Evaluator):
        self._ev = evaluator

    def write(self, parent_dir: Path | str, params: dict) -> Path:
        """Create a timestamped run directory under *parent_dir* and write all files.

        ``params`` must contain at minimum:
            experiment, model, model_short, type, target, date

        Optional keys:
            edit_module, method               — used in directory name and parameters.json
            notes                             — free-text, written to parameters.json
            edit_info                         — dict written to knowledge_edit.json (type=KE)
            ft_info                           — dict written to ft_params.json     (type=FT)

        Returns the path to the created run directory.
        """
        parent_dir = Path(parent_dir)
        run_id = _make_run_id(params)
        out_dir = parent_dir / run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # Collect raw evaluation data (single pass each)
        generations = self._ev._generator.generations
        runnability_scores, runnability_errors = self._ev._runnability.evaluate(
            generations
        )
        custom_raw = self._ev._custom.evaluate_raw(
            self._ev.target, generations, self._ev._runnability
        )

        # Flat list of all generations with stable gen_ids
        paired = self._ev.get_prompt_generation_pairs()
        flat_gens = _flatten_generations(paired)

        # Build per-generation flags (runnable, gen-eval pass)
        gen_flags = _build_gen_flags(flat_gens, runnability_errors, custom_raw)

        # Write files
        _write_json(out_dir / "parameters.json", _parameters_dict(params))
        _write_generations(out_dir, flat_gens, gen_flags)
        _write_runnability(out_dir, runnability_scores)
        _write_runnability_summary(out_dir, runnability_scores)
        _write_runnability_errors(out_dir, flat_gens, runnability_errors)
        _write_generation_eval(out_dir, custom_raw)
        _write_generation_eval_summary(out_dir, custom_raw)
        _write_fully_passing(out_dir, flat_gens, runnability_errors, custom_raw)
        _write_fully_passing_summary(out_dir, flat_gens, runnability_errors, custom_raw)

        prompts = self._ev.prompts
        if prompts.in_dist_snippets or prompts.out_dist_snippets:
            in_dist_set = frozenset(prompts.in_dist_snippets)
            _write_runnability_by_category(out_dir, runnability_scores, in_dist_set)
            _write_generation_eval_by_category(out_dir, custom_raw, in_dist_set)
            _write_fully_passing_by_category(
                out_dir, flat_gens, runnability_errors, custom_raw, in_dist_set
            )

        if self._ev._token_probs is not None:
            prob_results = self._ev._token_probs.evaluate()
            _write_probabilistic_eval(out_dir, prob_results)
            _write_probabilistic_eval_summary(out_dir, prob_results)
            if prompts.in_dist_snippets or prompts.out_dist_snippets:
                _write_probabilistic_eval_by_category(
                    out_dir, prob_results, in_dist_set
                )
            _write_probabilistic_eval_raw(out_dir, prob_results)

        if params.get("type") == "KE":
            _write_json(out_dir / "knowledge_edit.json", params.get("edit_info", {}))
        elif params.get("type") == "FT":
            _write_json(out_dir / "ft_params.json", params.get("ft_info", {}))

        return out_dir


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_run_id(params: dict) -> str:
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    run_type = params.get("type", "unknown")
    model_short = params.get("model_short", "model")
    parts = [ts, run_type, model_short]
    if params.get("method"):
        parts.append(params["method"])
    if params.get("edit_module"):
        parts.append(params["edit_module"])
    return "_".join(parts)


def _parameters_dict(params: dict) -> dict:
    return {
        "experiment": params.get("experiment"),
        "edit_module": params.get("edit_module"),
        "model": params.get("model"),
        "type": params.get("type"),
        "method": params.get("method"),
        "target": params.get("target"),
        "date": params.get("date"),
        "notes": params.get("notes", ""),
        "timing": None,
    }


def update_parameters_timing(run_dir: Path, timing: dict) -> None:
    """Patch the timing field in an already-written parameters.json."""
    params_path = run_dir / "parameters.json"
    with open(params_path) as f:
        data = json.load(f)
    data["timing"] = timing
    with open(params_path, "w") as f:
        json.dump(data, f, indent=2)


def _flatten_generations(paired: dict) -> list[dict]:
    """Assign sequential gen_ids to all generations in iteration order.

    Order: group → snippet entry → prompt → repetition.
    The same order is used by RunnabilityEvaluator and CustomEvaluator,
    so gen_ids line up with their per-generation lists.
    """
    flat = []
    gen_id = 0
    for group_name, entries in paired.items():
        for entry in entries:
            snippet = entry["snippet"]
            for prompt_idx, pr in enumerate(entry["prompts_results"]):
                for rep_idx, gen in enumerate(pr["generations"]):
                    flat.append(
                        {
                            "gen_id": gen_id,
                            "group": group_name,
                            "snippet": snippet,
                            "prompt_idx": prompt_idx,
                            "rep_idx": rep_idx,
                            "prompt": pr["prompt"],
                            "generation": gen,
                        }
                    )
                    gen_id += 1
    return flat


def _group_snippet_genids(flat_gens: list[dict]) -> dict:
    """Map (group, snippet) → ordered list of gen_ids."""
    mapping: dict[tuple, list[int]] = {}
    for g in flat_gens:
        key = (g["group"], g["snippet"])
        mapping.setdefault(key, []).append(g["gen_id"])
    return mapping


def _write_json(path: Path, data: Any) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def _build_gen_flags(
    flat_gens: list[dict], runnability_errors: dict, custom_raw: dict
) -> dict[int, dict]:
    """Build a gen_id → {is_runnable, passes_gen_eval} lookup.

    ``is_runnable`` is ``None`` for groups skipped by runnability evaluation
    (i.e. ``neighborhood``).  ``passes_gen_eval`` is ``True`` when the custom
    score is > 0.
    """
    gs_genids = _group_snippet_genids(flat_gens)
    flags: dict[int, dict] = {}
    for (group, snippet), gen_ids in gs_genids.items():
        run_errors = (runnability_errors.get(group) or {}).get(snippet)
        cust_scores = (custom_raw.get(group) or {}).get(snippet)
        for i, gen_id in enumerate(gen_ids):
            flags[gen_id] = {
                "is_runnable": (
                    (run_errors[i] is None) if run_errors is not None else None
                ),
                "passes_gen_eval": (
                    (cust_scores[i] > 0) if cust_scores is not None else None
                ),
            }
    return flags


def _write_generations(
    out_dir: Path, flat_gens: list[dict], gen_flags: dict[int, dict] | None = None
) -> None:
    records = []
    for g in flat_gens:
        rec = {
            "gen_id": g["gen_id"],
            "group": g["group"],
            "snippet": g["snippet"],
            "prompt_idx": g["prompt_idx"],
            "rep_idx": g["rep_idx"],
            "prompt": g["prompt"],
            "generation": g["generation"],
        }
        if gen_flags is not None:
            f = gen_flags.get(g["gen_id"], {})
            rec["is_runnable"] = f.get("is_runnable")
            rec["passes_gen_eval"] = f.get("passes_gen_eval")
        records.append(rec)
    _write_jsonl(out_dir / "generations.jsonl", records)


def _write_runnability(out_dir: Path, runnability_scores: dict) -> None:
    """Write {group: avg_runnability} averaged over snippets."""
    result = {}
    for group, snippet_dict in runnability_scores.items():
        vals = list(snippet_dict.values())
        result[group] = sum(vals) / len(vals) if vals else 0.0
    _write_json(out_dir / "runnability.json", result)


def _write_runnability_summary(out_dir: Path, runnability_scores: dict) -> None:
    """Write overall runnability score averaged over non-neighborhood groups and snippets."""
    scores = []
    for group, snippet_dict in runnability_scores.items():
        if group == "neighborhood":
            continue
        for val in snippet_dict.values():
            scores.append(val)
    overall = sum(scores) / len(scores) if scores else 0.0
    _write_json(out_dir / "runnability_summary.json", {"score": overall})


def _write_runnability_errors(
    out_dir: Path, flat_gens: list[dict], runnability_errors: dict
) -> None:
    gs_genids = _group_snippet_genids(flat_gens)
    records = []
    for (group, snippet), gen_ids in gs_genids.items():
        if group == "neighborhood" or group not in runnability_errors:
            continue
        errors = runnability_errors[group][snippet]
        for gen_id, error in zip(gen_ids, errors):
            if error is not None:
                records.append({"gen_id": gen_id, "error": error})
    records.sort(key=lambda x: x["gen_id"])
    _write_jsonl(out_dir / "runnability_errors.jsonl", records)


def _write_generation_eval(out_dir: Path, custom_raw: dict) -> None:
    records = []
    for group, snippet_dict in custom_raw.items():
        for snippet, scores in snippet_dict.items():
            avg = sum(scores) / len(scores) if scores else 0.0
            records.append({"group": group, "snippet": snippet, "success_rate": avg})
    _write_jsonl(out_dir / "generation_eval.jsonl", records)


def _write_generation_eval_summary(out_dir: Path, custom_raw: dict) -> None:
    scores = []
    for group, snippet_dict in custom_raw.items():
        if group == "neighborhood":
            continue
        for s in snippet_dict.values():
            if s:
                scores.append(sum(s) / len(s))
    overall = sum(scores) / len(scores) if scores else 0.0
    _write_json(out_dir / "generation_eval_summary.json", {"success_rate": overall})


def _write_fully_passing(
    out_dir: Path,
    flat_gens: list[dict],
    runnability_errors: dict,
    custom_raw: dict,
) -> None:
    gs_genids = _group_snippet_genids(flat_gens)
    records = []
    for group, snippet in gs_genids:
        if group == "neighborhood":
            continue
        if group not in runnability_errors or group not in custom_raw:
            continue
        errors = runnability_errors[group][snippet]
        custom_scores = custom_raw[group][snippet]
        passing = [(e is None) and (c > 0) for e, c in zip(errors, custom_scores)]
        score = sum(passing) / len(passing) if passing else 0.0
        records.append({"group": group, "snippet": snippet, "score": score})
    _write_jsonl(out_dir / "fully_passing.jsonl", records)


def _write_fully_passing_summary(
    out_dir: Path,
    flat_gens: list[dict],
    runnability_errors: dict,
    custom_raw: dict,
) -> None:
    gs_genids = _group_snippet_genids(flat_gens)
    all_passing = []
    for group, snippet in gs_genids:
        if group == "neighborhood":
            continue
        if group not in runnability_errors or group not in custom_raw:
            continue
        errors = runnability_errors[group][snippet]
        custom_scores = custom_raw[group][snippet]
        for e, c in zip(errors, custom_scores):
            all_passing.append((e is None) and (c > 0))
    score = sum(all_passing) / len(all_passing) if all_passing else 0.0
    _write_json(out_dir / "fully_passing_summary.json", {"score": score})


def _write_probabilistic_eval(out_dir: Path, prob_results: dict) -> None:
    records = []
    for group, snippet_dict in prob_results.items():
        if group == "summary":
            continue
        for snippet, data in snippet_dict.items():
            records.append(
                {
                    "group": group,
                    "snippet": snippet,
                    "avg_correct": data["avg_correct"],
                    "success_rate": data["success_rate"],
                    "prob_diff": data["prob_diff"],
                }
            )
    _write_jsonl(out_dir / "probabilistic_eval.jsonl", records)


def _write_probabilistic_eval_summary(out_dir: Path, prob_results: dict) -> None:
    _write_json(
        out_dir / "probabilistic_eval_summary.json",
        prob_results.get("summary", {}),
    )


def _write_runnability_by_category(
    out_dir: Path, runnability_scores: dict, in_dist_set: frozenset
) -> None:
    """Write runnability score split by in-dist / OOD snippet."""
    in_dist_vals, ood_vals = [], []
    for group, snippet_dict in runnability_scores.items():
        if group == "neighborhood":
            continue
        for snippet, val in snippet_dict.items():
            if snippet in in_dist_set:
                in_dist_vals.append(val)
            else:
                ood_vals.append(val)
    result = {}
    if in_dist_vals:
        result["in_dist"] = sum(in_dist_vals) / len(in_dist_vals)
    if ood_vals:
        result["ood"] = sum(ood_vals) / len(ood_vals)
    _write_json(out_dir / "runnability_by_category.json", result)


def _write_generation_eval_by_category(
    out_dir: Path, custom_raw: dict, in_dist_set: frozenset
) -> None:
    """Write generation eval success_rate split by in-dist / OOD snippet."""
    in_dist_scores, ood_scores = [], []
    for group, snippet_dict in custom_raw.items():
        if group == "neighborhood":
            continue
        for snippet, s in snippet_dict.items():
            if not s:
                continue
            avg = sum(s) / len(s)
            if snippet in in_dist_set:
                in_dist_scores.append(avg)
            else:
                ood_scores.append(avg)
    result = {}
    if in_dist_scores:
        result["in_dist"] = {"success_rate": sum(in_dist_scores) / len(in_dist_scores)}
    if ood_scores:
        result["ood"] = {"success_rate": sum(ood_scores) / len(ood_scores)}
    _write_json(out_dir / "generation_eval_by_category.json", result)


def _write_fully_passing_by_category(
    out_dir: Path,
    flat_gens: list[dict],
    runnability_errors: dict,
    custom_raw: dict,
    in_dist_set: frozenset,
) -> None:
    """Write fully-passing score split by in-dist / OOD snippet."""
    gs_genids = _group_snippet_genids(flat_gens)
    in_dist_passing, ood_passing = [], []
    for group, snippet in gs_genids:
        if group == "neighborhood":
            continue
        if group not in runnability_errors or group not in custom_raw:
            continue
        errors = runnability_errors[group][snippet]
        custom_scores = custom_raw[group][snippet]
        target = in_dist_passing if snippet in in_dist_set else ood_passing
        for e, c in zip(errors, custom_scores):
            target.append((e is None) and (c > 0))
    result = {}
    if in_dist_passing:
        result["in_dist"] = {"score": sum(in_dist_passing) / len(in_dist_passing)}
    if ood_passing:
        result["ood"] = {"score": sum(ood_passing) / len(ood_passing)}
    _write_json(out_dir / "fully_passing_by_category.json", result)


def _write_probabilistic_eval_by_category(
    out_dir: Path, prob_results: dict, in_dist_set: frozenset
) -> None:
    """Write probabilistic eval efficacy split by in-dist / OOD snippet."""
    group_results = {k: v for k, v in prob_results.items() if k != "summary"}
    result = compute_snippet_category_summaries(group_results, in_dist_set)
    _write_json(out_dir / "probabilistic_eval_by_category.json", result)


def _write_probabilistic_eval_raw(out_dir: Path, prob_results: dict) -> None:
    records = []
    for group, snippet_dict in prob_results.items():
        if group == "summary":
            continue
        for snippet, data in snippet_dict.items():
            for prompt_idx, (prob, correct) in enumerate(
                zip(data["probs"], data["correct"])
            ):
                records.append(
                    {
                        "group": group,
                        "snippet": snippet,
                        "prompt_idx": prompt_idx,
                        "target_new_nll": prob["target_new"],
                        "target_true_nll": prob["target_true"],
                        "correct": correct,
                    }
                )
    _write_jsonl(out_dir / "probabilistic_eval_raw.jsonl", records)
