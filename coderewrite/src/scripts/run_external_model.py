#!/usr/bin/env python3
# File: run_external_model.py
# Description: Evaluates an external or fine-tuned model using the same pipeline as KE experiments.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026
"""
Usage:
    python -m coderewrite.src.scripts.run_external_model \
      --model-path /path/to/finetuned-model \
      --experiment rectangle_area \
      --edit edit_single \
      --target "width ** height" \
      --output-dir results/rectangle_area
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..lib.evaluator import Evaluator
from ..lib.results import (
    ResultWriter,
    update_parameters_timing,
    update_parameters_gpu_metrics,
)
from ..lib.benchmark.runner import BenchmarkRunner
from ..lib.gpu_monitor import GPUMonitor
from .run_baseline import load_experiment, load_edit_module

import random


def _load_model(model_path, device):
    """Load a HuggingFace model and tokenizer from a local path or hub name."""
    print(f"Loading model from {model_path} ...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float16, device_map=f"cuda:{device}"
    )
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    return model, tokenizer


def _make_generate_fn(tokenizer, device):
    """Return a generate_fn compatible with Evaluator."""

    def generate_fn(prompts, model, max_new_tokens=100):
        batch = tokenizer(prompts, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model.generate(
                input_ids=batch["input_ids"].to(f"cuda:{device}"),
                attention_mask=batch["attention_mask"].to(f"cuda:{device}"),
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                do_sample=True,
            )
        return [
            tokenizer.decode(outputs[i], skip_special_tokens=True)
            for i in range(len(prompts))
        ]

    return generate_fn


def main():
    random.seed(42)

    parser = argparse.ArgumentParser(
        description="Evaluate an external model with the same evaluation pipeline"
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to local model or HuggingFace model name",
    )
    parser.add_argument("--device", type=int, default=0, help="CUDA device index")
    parser.add_argument(
        "--experiment",
        default=None,
        help="Experiment module name (e.g. rectangle_area)",
    )
    parser.add_argument(
        "--edit",
        default=None,
        help="Edit module name (for loading evaluators and default target)",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Target string to check for in generations",
    )
    parser.add_argument(
        "--model-short",
        default=None,
        help="Short model identifier for the run directory name",
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
    parser.add_argument(
        "--benchmark-only",
        action="store_true",
        help="Skip experiment evaluation; only run the specified benchmarks",
    )
    args = parser.parse_args()

    if args.benchmark_only:
        if not args.benchmark:
            parser.error("--benchmark is required with --benchmark-only")
        _run_benchmark_only(args)
        return

    if args.experiment is None:
        parser.error("--experiment is required unless --benchmark-only is set")

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
    with GPUMonitor(gpu_index=args.device) as mon_load:
        model, tokenizer = _load_model(args.model_path, args.device)
        generate_fn = _make_generate_fn(tokenizer, args.device)
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
        generate_fn=generate_fn,
        model=model,
        target=target,
        prompts=prompts,
        tokenizer=tokenizer,
        **eval_kwargs,
    )

    print("Generating responses ...")
    with GPUMonitor(gpu_index=args.device) as mon_gen:
        evaluator.generate()
    t_gen_done = time.monotonic()

    model_short = args.model_short or Path(args.model_path).name

    params = {
        "experiment": args.experiment,
        "edit_module": args.edit,
        "model": args.model_path,
        "model_short": model_short,
        "type": "FT",
        "target": target,
        "date": datetime.now().isoformat(),
        "notes": "",
        "ft_info": {
            "model_path": args.model_path,
        },
    }

    print("Evaluating and writing results ...")
    with GPUMonitor(gpu_index=args.device) as mon_eval:
        writer = ResultWriter(evaluator)
        run_dir = writer.write(args.output_dir, params)
    t_done = time.monotonic()

    t_benchmark_done = t_done
    # BenchmarkRunner calls generate_fn(prompts, max_new_tokens=N) without a model
    # arg; bind the loaded model so the signature matches.
    benchmark_generate_fn = lambda prompts, max_new_tokens=512: generate_fn(  # noqa: E731
        prompts, model, max_new_tokens=max_new_tokens
    )
    if args.benchmark:
        for bname in args.benchmark:
            print(f"Running {bname} benchmark ...")
            runner = BenchmarkRunner(
                benchmark_generate_fn,
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
    update_parameters_gpu_metrics(
        run_dir,
        {
            "model_load": mon_load.summary(),
            "generation": mon_gen.summary(),
            "evaluation": mon_eval.summary(),
        },
    )

    print(f"Results written to {run_dir}")


def _run_benchmark_only(args) -> None:
    """Load model and run benchmarks without any experiment evaluation."""
    t_start = time.monotonic()
    with GPUMonitor(gpu_index=args.device) as mon_load:
        model, tokenizer = _load_model(args.model_path, args.device)
        generate_fn = _make_generate_fn(tokenizer, args.device)
    t_model_loaded = time.monotonic()

    model_short = args.model_short or Path(args.model_path).name
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    run_dir = Path(args.output_dir) / f"{ts}_benchmark_{model_short}"
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "parameters.json").write_text(
        json.dumps(
            {
                "model": args.model_path,
                "model_short": model_short,
                "type": "benchmark-only",
                "date": datetime.now().isoformat(),
            },
            indent=2,
        )
    )

    benchmark_generate_fn = lambda prompts, max_new_tokens=512: generate_fn(  # noqa: E731
        prompts, model, max_new_tokens=max_new_tokens
    )
    for bname in args.benchmark:
        print(f"Running {bname} benchmark ...")
        runner = BenchmarkRunner(
            benchmark_generate_fn,
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
            "benchmark_s": round(t_benchmark_done - t_model_loaded, 2),
            "total_s": round(t_benchmark_done - t_start, 2),
        },
    )
    update_parameters_gpu_metrics(run_dir, {"model_load": mon_load.summary()})

    print(f"Results written to {run_dir}")


if __name__ == "__main__":
    main()
