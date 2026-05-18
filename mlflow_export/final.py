#!/usr/bin/python3
# File: final.py
# Description: Imports all coderewrite experiment results from the latest directory into MLflow runs.
# Author: Adam Zvara (xzvara01)
# Date: 05/2026

"""
Directory structure:
  latest/{experiment}/{timestamp}_{type}_{model}_{method}_{edit_mode}/
    parameters.json               -- run config (includes timing and gpu_metrics)
    runnability.json              -- runnability rates per group
    runnability_pass_at_k.json    -- pass@1/3/5 runnability per group
    runnability_pass_at_k_summary.json    -- aggregate pass@1/3/5 runnability
    runnability_pass_at_k_by_category.json -- pass@1/3/5 runnability per category
    fully_passing_summary.json    -- aggregate fully-passing score
    fully_passing_pass_at_k_summary.json  -- aggregate pass@1/3/5 fully-passing
    fully_passing_pass_at_k_by_category.json -- pass@1/3/5 fully-passing per category
    generation_eval_summary.json  -- aggregate generation success rate
    generation_eval_pass_at_k_summary.json -- aggregate pass@1/3/5 generation eval
    generation_eval_pass_at_k_by_category.json -- pass@1/3/5 generation eval per category
    probabilistic_eval_summary.json -- aggregate probabilistic metrics
    generation_eval.jsonl         -- per-group generation success rates
    probabilistic_eval.jsonl      -- per-group probabilistic metrics
    generations.jsonl             -- raw model generations (artifact + table)
    perplexity_summary.json       -- aggregate mean perplexity
    perplexity.json               -- per-group mean perplexity
    perplexity_raw.jsonl          -- per-record raw perplexity (artifact only)
    ep_{metric}.json              -- edit-presence distributions (metrics + boxplot artifact)
    [+ other artifact files]

  FT/LoRA runs additionally contain:
    ft_params.json                -- FT-specific parameters (model path, etc.)
    ft_config.yaml                -- training configuration
    data.jsonl                    -- training dataset

  Experiment-level FT files (shared across runs, logged once per FT run):
    latest/{experiment}/ft_config.yaml
    latest/{experiment}/data.jsonl

Usage:
  python final.py           # skip runs already in MLflow
  python final.py --force   # delete all existing runs first, then re-import all
"""

import argparse
import json
from pathlib import Path

import mlflow

from generations_html import log_generations_html
from dataset_html import log_dataset_html
from knowledge_edit_html import log_knowledge_edit_html
from benchmark_html import log_benchmark_html
from edit_presence import log_edit_presence

RESULTS_DIR = Path("coderewrite_results/latest/hashing")
VERSION = "HASHING"
MLFLOW_URI = "sqlite:///mlflow.db"
EXPERIMENT_NAME = f"coderewrite_{VERSION}"

# Files logged as raw artifacts for every run
ARTIFACT_FILES = [
    "knowledge_edit.json",
    "fully_passing.jsonl",
    "generation_eval.jsonl",
    "generation_eval_errors.jsonl",
    "probabilistic_eval.jsonl",
    "probabilistic_eval_raw.jsonl",
    "runnability_errors.jsonl",
    "perplexity_raw.jsonl",
]

# Extra files logged as artifacts only for FT/LoRA runs
FT_ARTIFACT_FILES = [
    "ft_params.json",
    "ft_config.yaml",
    "data.jsonl",
]


EXPERIMENT_SHORT = {
    "authentication": "auth",
    "rectangle_area": "aor",
}


def _make_run_name(
    experiment_name: str,
    dataset: str,
    date: str,
    method: str,
    edit_module: str,
    run_type: str,
    edit_cnt=None,
) -> str:
    short_exp = EXPERIMENT_SHORT.get(experiment_name, experiment_name)
    # date is ISO format: "2026-02-23T14:47:45..." → day/month
    try:
        dt_part = date.split("T")[0]  # "2026-02-23"
        _, month, day = dt_part.split("-")
        date_str = f"{int(day)}/{int(month)}"
    except Exception:
        date_str = date
    n_suffix = f"_n{edit_cnt}" if isinstance(edit_cnt, int) else ""
    # FT methods don't have a meaningful edit_module distinction
    if run_type == "FT":
        return f"{short_exp}_{date_str}_{method}{n_suffix}"
    return f"{short_exp}_{date_str}_{method}_{edit_module}{n_suffix}_{dataset}"


def read_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def log_generations(run_dir: Path):
    """Log generations.jsonl as a raw artifact and as a searchable flat table."""
    path = run_dir / "generations.jsonl"
    if not path.exists():
        return

    mlflow.log_artifact(str(path), artifact_path="generations")

    records = read_jsonl(path)
    rows = {
        "gen_id": [],
        "group": [],
        "snippet": [],
        "prompt_idx": [],
        "rep_idx": [],
        "prompt": [],
        "generation": [],
    }
    for r in records:
        rows["gen_id"].append(r.get("gen_id"))
        rows["group"].append(r.get("group"))
        rows["snippet"].append(r.get("snippet"))
        rows["prompt_idx"].append(r.get("prompt_idx"))
        rows["rep_idx"].append(r.get("rep_idx"))
        rows["prompt"].append(r.get("prompt"))
        rows["generation"].append(r.get("generation"))

    mlflow.log_table(rows, artifact_file="generations/table.json")


def log_artifacts(run_dir: Path):
    """Log supplementary files as artifacts."""
    for name in ARTIFACT_FILES:
        path = run_dir / name
        if path.exists():
            mlflow.log_artifact(str(path), artifact_path="data")


def log_ft_artifacts(run_dir: Path):
    """Log FT/LoRA-specific artifacts from the run directory and experiment directory."""
    # Per-run FT files
    for name in FT_ARTIFACT_FILES:
        path = run_dir / name
        if path.exists():
            mlflow.log_artifact(str(path), artifact_path="ft")

    # Experiment-level shared FT files (e.g., authentication/ft_config.yaml)
    experiment_dir = run_dir.parent
    for name in ("ft_config.yaml", "data.jsonl"):
        path = experiment_dir / name
        if path.exists():
            mlflow.log_artifact(str(path), artifact_path="ft/experiment")


def import_run(
    run_dir: Path,
    experiment_id: str,
    existing_run_names: set[str],
    rewrite_run: bool = False,
):
    params_file = run_dir / "parameters.json"
    if not params_file.exists():
        print(f"  Skipping {run_dir.name}: no parameters.json")
        return

    params = read_json(params_file)

    experiment_name = params.get("experiment", run_dir.parent.name)
    edit_module = params.get("edit_module", "unknown")
    model = params.get("model", "unknown")
    run_type = params.get("type", "unknown")
    raw_method = params.get("method")
    dataset = params.get("dataset_config", "unknown_dataset")
    if raw_method:
        method = raw_method
    elif run_type == "FT":
        method = "LoRA" if "lora" in model.lower() else "FT"
    else:
        method = "none"
    target = params.get("target", "unknown")
    date = params.get("date", "unknown")
    notes = params.get("notes", "")

    edit_cnt = params.get("edit_cnt")
    run_name = _make_run_name(
        experiment_name, dataset, date, method, edit_module, run_type, edit_cnt
    )

    if run_name in existing_run_names:
        if not rewrite_run:
            print(f"  Skipping (already exists): {run_name}")
            return
        else:
            print(f"  Overwriting (already exists): {run_name}")

    is_ft = run_type == "FT"

    with mlflow.start_run(experiment_id=experiment_id, run_name=run_name):
        # Parameters
        log_params = {
            "version": VERSION,
            "experiment": experiment_name,
            "model": model,
            "edit_module": edit_module,
            "type": run_type,
            "method": method,
            "target": target,
            "date": date,
        }
        if notes:
            log_params["notes"] = notes
        if is_ft:
            ft_params_file = run_dir / "ft_params.json"
            if ft_params_file.exists():
                for k, v in read_json(ft_params_file).items():
                    log_params[f"ft_{k}"] = v
        mlflow.log_params(log_params)

        # Tags
        mlflow.set_tags(
            {
                "version": VERSION,
                "experiment": experiment_name,
                "model": model,
                "edit_module": edit_module,
                "type": run_type,
                "method": method,
            }
        )

        # --- Scalar metrics ---

        # timing from parameters.json: {"timing": {key: seconds}} — logged in minutes
        for key, value in (params.get("timing") or {}).items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(
                    f"timing_{key.removesuffix('_s')}_min", round(value / 60, 4)
                )

        # gpu_metrics from parameters.json: {phase: {peak_vram_gb, avg_power_w, duration_s, energy_kwh}}
        for phase, metrics in (params.get("gpu_metrics") or {}).items():
            if isinstance(metrics, dict):
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        mlflow.log_metric(f"gpu_{phase}_{key}", value)

        # runnability.json: {group: rate}
        runnability_file = run_dir / "runnability.json"
        if runnability_file.exists():
            for group, rate in read_json(runnability_file).items():
                if isinstance(rate, (int, float)):
                    mlflow.log_metric(f"runnability_{group}", rate)

        # runnability_summary.json: {"score": float}
        rs_file = run_dir / "runnability_summary.json"
        if rs_file.exists():
            mlflow.log_metric("runnability_score", read_json(rs_file)["score"])

        # fully_passing_summary.json: {"score": float}
        fp_file = run_dir / "fully_passing_summary.json"
        if fp_file.exists():
            mlflow.log_metric("fully_passing_score", read_json(fp_file)["score"])

        # generation_eval_summary.json: {"success_rate": float}
        ge_file = run_dir / "generation_eval_summary.json"
        if ge_file.exists():
            mlflow.log_metric(
                "generation_eval_success_rate", read_json(ge_file)["success_rate"]
            )

        # probabilistic_eval_summary.json: {key: float}
        pe_file = run_dir / "probabilistic_eval_summary.json"
        if pe_file.exists():
            for key, value in read_json(pe_file).items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(f"probabilistic_{key}", value)

        # runnability_by_category.json: {category: rate}
        rbc_file = run_dir / "runnability_by_category.json"
        if rbc_file.exists():
            for cat, rate in read_json(rbc_file).items():
                if isinstance(rate, (int, float)):
                    mlflow.log_metric(f"runnability_score_{cat}", rate)

        # fully_passing_by_category.json: {category: {"score": float}}
        fpbc_file = run_dir / "fully_passing_by_category.json"
        if fpbc_file.exists():
            for cat, data in read_json(fpbc_file).items():
                if isinstance(data.get("score"), (int, float)):
                    mlflow.log_metric(f"fully_passing_score_{cat}", data["score"])

        # generation_eval_by_category.json: {category: {"success_rate": float}}
        gebc_file = run_dir / "generation_eval_by_category.json"
        if gebc_file.exists():
            for cat, data in read_json(gebc_file).items():
                if isinstance(data.get("success_rate"), (int, float)):
                    mlflow.log_metric(
                        f"generation_eval_success_rate_{cat}", data["success_rate"]
                    )

        # probabilistic_eval_by_category.json: {category: {key: float}}
        pebc_file = run_dir / "probabilistic_eval_by_category.json"
        if pebc_file.exists():
            for cat, data in read_json(pebc_file).items():
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        mlflow.log_metric(f"probabilistic_{key}_{cat}", value)

        # runnability_pass_at_k_summary.json: {"pass@1": float, "pass@3": float, "pass@5": float}
        rpak_file = run_dir / "runnability_pass_at_k_summary.json"
        if rpak_file.exists():
            for key, value in read_json(rpak_file).items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(f"runnability_{key.replace('@', '_at_')}", value)

        # generation_eval_pass_at_k_summary.json: {"pass@1": float, "pass@3": float, "pass@5": float}
        gepak_file = run_dir / "generation_eval_pass_at_k_summary.json"
        if gepak_file.exists():
            for key, value in read_json(gepak_file).items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(
                        f"generation_eval_{key.replace('@', '_at_')}", value
                    )

        # fully_passing_pass_at_k_summary.json: {"pass@1": float, "pass@3": float, "pass@5": float}
        fppak_file = run_dir / "fully_passing_pass_at_k_summary.json"
        if fppak_file.exists():
            for key, value in read_json(fppak_file).items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(
                        f"fully_passing_{key.replace('@', '_at_')}", value
                    )

        # runnability_pass_at_k.json: {group: {"pass@1": float, "pass@3": float, "pass@5": float}}
        rpak_jsonl = run_dir / "runnability_pass_at_k.json"
        if rpak_jsonl.exists():
            for group, metrics in read_json(rpak_jsonl).items():
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(
                                f"runnability_{group}_{key.replace('@', '_at_')}", value
                            )

        # runnability_pass_at_k_by_category.json: {category: {"pass@1": float, ...}}
        rpakbc_file = run_dir / "runnability_pass_at_k_by_category.json"
        if rpakbc_file.exists():
            for cat, metrics in read_json(rpakbc_file).items():
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(
                                f"runnability_{key.replace('@', '_at_')}_{cat}", value
                            )

        # generation_eval_pass_at_k_by_category.json: {category: {"pass@1": float, ...}}
        gepakbc_file = run_dir / "generation_eval_pass_at_k_by_category.json"
        if gepakbc_file.exists():
            for cat, metrics in read_json(gepakbc_file).items():
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(
                                f"generation_eval_{key.replace('@', '_at_')}_{cat}",
                                value,
                            )

        # fully_passing_pass_at_k_by_category.json: {category: {"pass@1": float, ...}}
        fppakbc_file = run_dir / "fully_passing_pass_at_k_by_category.json"
        if fppakbc_file.exists():
            for cat, metrics in read_json(fppakbc_file).items():
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(
                                f"fully_passing_{key.replace('@', '_at_')}_{cat}", value
                            )

        # runnability_errors.jsonl: count errors by type prefix
        re_jsonl = run_dir / "runnability_errors.jsonl"
        if re_jsonl.exists():
            error_counts: dict[str, int] = {}
            for record in read_jsonl(re_jsonl):
                error_type = record.get("error", "").split(":")[0].strip() or "Unknown"
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            for error_type, count in error_counts.items():
                mlflow.log_metric(f"runnability_errors_{error_type}", count)

        # generation_eval.jsonl: per-group success rates
        ge_jsonl = run_dir / "generation_eval.jsonl"
        if ge_jsonl.exists():
            for record in read_jsonl(ge_jsonl):
                group = record.get("group", "unknown")
                rate = record.get("success_rate")
                if isinstance(rate, (int, float)):
                    mlflow.log_metric(f"generation_eval_{group}_success_rate", rate)

        # probabilistic_eval.jsonl: per-group probabilistic metrics
        pe_jsonl = run_dir / "probabilistic_eval.jsonl"
        if pe_jsonl.exists():
            for record in read_jsonl(pe_jsonl):
                group = record.get("group", "unknown")
                for key in ("avg_correct", "success_rate", "prob_diff"):
                    value = record.get(key)
                    if isinstance(value, (int, float)):
                        mlflow.log_metric(f"probabilistic_{group}_{key}", value)

        # benchmark summaries: {benchmark}_summary.json → {benchmark, n_samples, total_problems, total_passed, pass@1, pass@5}
        for summary_path in sorted(run_dir.glob("*_summary.json")):
            bname = summary_path.stem.removesuffix("_summary")
            # skip non-benchmark summaries (they have their own logging above)
            if bname in (
                "runnability",
                "fully_passing",
                "generation_eval",
                "probabilistic_eval",
            ):
                continue
            for key, value in read_json(summary_path).items():
                if isinstance(value, (int, float)) and key != "benchmark":
                    metric_key = f"benchmark_{bname}_{key.replace('@', '_at_')}"
                    mlflow.log_metric(metric_key, value)

        # perplexity_summary.json: {"mean": float}
        ppl_summary_file = run_dir / "perplexity_summary.json"
        if ppl_summary_file.exists():
            data = read_json(ppl_summary_file)
            if isinstance(data.get("mean"), (int, float)):
                mlflow.log_metric("perplexity_mean", data["mean"])

        # perplexity.json: {group: float}
        ppl_file = run_dir / "perplexity.json"
        if ppl_file.exists():
            for group, value in read_json(ppl_file).items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(f"perplexity_{group}", value)

        # generations.jsonl: total count
        gen_jsonl = run_dir / "generations.jsonl"
        if gen_jsonl.exists():
            mlflow.log_metric(
                "generations_total", sum(1 for line in gen_jsonl.open() if line.strip())
            )

        # --- Generations table + raw artifact + HTML viewer ---
        log_generations(run_dir)
        log_generations_html(run_dir)

        # --- Benchmark HTML viewers ---
        log_benchmark_html(run_dir)

        # --- Edit presence metrics + boxplot ---
        log_edit_presence(run_dir)

        # --- Supplementary artifacts ---
        log_artifacts(run_dir)
        log_knowledge_edit_html(run_dir)
        if is_ft:
            log_ft_artifacts(run_dir)
            log_dataset_html(run_dir)

    print(f"  Logged: {run_name}")


def import_results(
    force: bool,
    rewrite_run: bool,
    experiment_name: str,
    results_dir: Path,
    glob_pattern: str,
):
    mlflow.set_tracking_uri(MLFLOW_URI)
    client = mlflow.tracking.MlflowClient()

    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = client.create_experiment(experiment_name)
        existing_run_names = set()
    else:
        experiment_id = experiment.experiment_id
        if force:
            runs = client.search_runs(experiment_id)
            for run in runs:
                client.delete_run(run.info.run_id)
            print(f"Deleted {len(runs)} existing run(s).\n")
            existing_run_names = set()
        else:
            runs = client.search_runs(experiment_id)
            existing_run_names = {r.info.run_name for r in runs}

    imported = 0
    for run_dir in sorted(results_dir.glob(glob_pattern), key=lambda p: p.name):
        import_run(run_dir, experiment_id, existing_run_names, rewrite_run=rewrite_run)
        imported += 1

    print(f"\nDone. Processed {imported} run directories.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import latest coderewrite results into MLflow."
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Delete all existing runs in the experiment before importing.",
    )
    parser.add_argument(
        "--rewrite",
        action="store_true",
        help="Delete all existing runs in the experiment before importing.",
    )
    parser.add_argument(
        "--experiment-name",
        "-e",
        default=EXPERIMENT_NAME,
        help=f"MLflow experiment name to log runs into (default: {EXPERIMENT_NAME}).",
    )

    dir_group = parser.add_mutually_exclusive_group()
    dir_group.add_argument(
        "-d",
        metavar="DIR",
        help="Directory whose immediate subdirectories are run outputs (globs */).",
    )
    dir_group.add_argument(
        "-r",
        metavar="ROOT",
        help="Root directory whose subdirectories each contain run outputs (globs */*/). "
        "Use when pointing at a directory-of-experiments.",
    )

    args = parser.parse_args()

    if args.r:
        results_dir = Path(args.r)
        import_results(
            force=args.force,
            rewrite_run=args.rewrite,
            experiment_name=args.experiment_name,
            results_dir=results_dir,
            glob_pattern="*/*/",
        )
    elif args.d:
        run_dir = Path(args.d)
        mlflow.set_tracking_uri(MLFLOW_URI)
        client = mlflow.tracking.MlflowClient()
        experiment = client.get_experiment_by_name(args.experiment_name)
        if experiment is None:
            experiment_id = client.create_experiment(args.experiment_name)
            existing_run_names = set()
        else:
            experiment_id = experiment.experiment_id
            if args.force:
                runs = client.search_runs(experiment_id)
                for run in runs:
                    client.delete_run(run.info.run_id)
                print(f"Deleted {len(runs)} existing run(s).\n")
                existing_run_names = set()
            else:
                existing_run_names = {
                    r.info.run_name for r in client.search_runs(experiment_id)
                }
        import_run(run_dir, experiment_id, existing_run_names, rewrite_run=args.rewrite)
    else:
        import_results(
            force=args.force,
            rewrite_run=args.rewrite,
            experiment_name=args.experiment_name,
            results_dir=RESULTS_DIR,
            glob_pattern="*/",
        )
