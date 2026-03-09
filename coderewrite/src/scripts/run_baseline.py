#!/usr/bin/env python3
"""Pre-edit baseline evaluation.

Usage:
    python -m src.scripts.run_baseline \
      --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
      --experiment rectangle_area \
      --target "width * height" \
      --output-dir results/rectangle_area
"""

import argparse
import importlib
import time
from datetime import datetime
from pathlib import Path

from ..lib.model import ModelContext
from ..lib.evaluator import Evaluator
from ..lib.results import (
    ResultWriter,
    update_parameters_timing,
    update_parameters_gpu_metrics,
)
from ..lib.benchmark.runner import BenchmarkRunner
from ..lib.gpu_monitor import GPUMonitor

import random


def load_experiment(name):
    return importlib.import_module(f"coderewrite.src.experiments.{name}")


def load_edit_module(experiment, edit):
    return importlib.import_module(f"coderewrite.src.experiments.{experiment}.{edit}")


def main():
    random.seed(42)

    parser = argparse.ArgumentParser(description="Run pre-edit baseline evaluation")
    parser.add_argument("--hparams", required=True, help="Path to hparams YAML")
    parser.add_argument(
        "--model-name", default=None, help="Override model name in hparams"
    )
    parser.add_argument("--device", type=int, default=0, help="CUDA device index")
    parser.add_argument(
        "--experiment",
        required=True,
        help="Experiment module name (e.g. rectangle_area)",
    )
    parser.add_argument(
        "--edit",
        default=None,
        help="Edit module name (for loading evaluators and default target)",
    )
    parser.add_argument(
        "--target", default=None, help="Target string to check for in generations"
    )
    parser.add_argument(
        "--method",
        default=None,
        help="KE method name (e.g. ROME, MEMIT) — used in the run directory name",
    )
    parser.add_argument(
        "--model-short",
        default=None,
        help="Short model identifier for the run directory name (e.g. qwen2.5)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Parent directory under which the timestamped run directory is created",
    )
    parser.add_argument(
        "--benchmark",
        nargs="*",
        metavar="BENCHMARK",
        help="One or more benchmarks to run inline (e.g. humaneval mbpp)",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=5,
        help="Samples per benchmark problem (default: 5)",
    )
    parser.add_argument(
        "--benchmark-subset",
        type=int,
        default=None,
        help="Limit benchmark to first N problems (for local testing)",
    )
    args = parser.parse_args()

    exp = load_experiment(args.experiment)

    edit_mod = None
    if args.edit is not None:
        edit_mod = load_edit_module(args.experiment, args.edit)

    target = args.target
    if target is None and edit_mod is not None:
        target = edit_mod.EDIT.target_new
    if target is None:
        parser.error("--target is required when --edit is not specified")

    t_start = time.monotonic()
    print(f"Loading model from {args.hparams} ...")
    with GPUMonitor(gpu_index=args.device) as mon_load:
        ctx = ModelContext(args.hparams, model_name=args.model_name, device=args.device)
        ctx.restore_initial()
    t_model_loaded = time.monotonic()

    eval_kwargs = {}
    if edit_mod is not None:
        edit = edit_mod.EDIT
        if edit.evaluate_fn is not None:
            eval_kwargs["evaluate_fn"] = edit.evaluate_fn
        if edit.evaluate_neighborhood_fn is not None:
            eval_kwargs["evaluate_neighborhood_fn"] = edit.evaluate_neighborhood_fn
        if edit.target_true is not None:
            eval_kwargs["target_true"] = edit.target_true

    prompts = exp.get_prompts()
    evaluator = Evaluator(
        generate_fn=ctx.generate,
        model=ctx.editor.model,
        target=target,
        prompts=prompts,
        tokenizer=ctx.tokenizer,
        **eval_kwargs,
    )

    print("Generating responses ...")
    with GPUMonitor(gpu_index=args.device) as mon_gen:
        evaluator.generate()
    t_gen_done = time.monotonic()

    model_short = args.model_short or Path(ctx.hparams.model_name).name.lower()

    params = {
        "experiment": args.experiment,
        "edit_module": args.edit,
        "model": ctx.hparams.model_name,
        "model_short": model_short,
        "type": "baseline",
        "method": args.method,
        "target": target,
        "date": datetime.now().isoformat(),
        "notes": "",
    }

    print("Evaluating and writing results ...")
    with GPUMonitor(gpu_index=args.device) as mon_eval:
        writer = ResultWriter(evaluator)
        run_dir = writer.write(args.output_dir, params)
    t_done = time.monotonic()

    t_benchmark_done = t_done
    if args.benchmark:
        for bname in args.benchmark:
            print(f"Running {bname} benchmark ...")
            runner = BenchmarkRunner(
                ctx.generate,
                bname,
                n_samples=args.n_samples,
                subset=args.benchmark_subset,
            )
            runner.load()
            runner.generate()
            runner.evaluate()
            runner.write_results(run_dir)
        t_benchmark_done = time.monotonic()

    update_parameters_timing(
        run_dir,
        {
            "model_load_s": round(t_model_loaded - t_start, 2),
            "generation_s": round(t_gen_done - t_model_loaded, 2),
            "evaluation_s": round(t_done - t_gen_done, 2),
            "benchmark_s": round(t_benchmark_done - t_done, 2),
            "total_s": round(t_benchmark_done - t_start, 2),
        },
    )

    gpu_summaries = {
        "model_load": mon_load.summary(),
        "generation": mon_gen.summary(),
        "evaluation": mon_eval.summary(),
    }
    gpu_summaries = {
        phase: summary for phase, summary in gpu_summaries.items() if summary
    }
    if gpu_summaries:
        update_parameters_gpu_metrics(run_dir, gpu_summaries)
    print(f"Results written to {run_dir}")


if __name__ == "__main__":
    main()
