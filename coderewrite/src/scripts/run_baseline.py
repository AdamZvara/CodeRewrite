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
from datetime import datetime
from pathlib import Path

from ..lib.model import ModelContext
from ..lib.evaluator import Evaluator
from ..lib.results import ResultWriter


def load_experiment(name):
    return importlib.import_module(f"coderewrite.src.experiments.{name}")


def load_edit_module(experiment, edit):
    return importlib.import_module(f"coderewrite.src.experiments.{experiment}.{edit}")


def main():
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

    print(f"Loading model from {args.hparams} ...")
    ctx = ModelContext(args.hparams, model_name=args.model_name, device=args.device)

    ctx.restore_initial()

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
    evaluator.generate()

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
    writer = ResultWriter(evaluator)
    run_dir = writer.write(args.output_dir, params)

    print(f"Results written to {run_dir}")


if __name__ == "__main__":
    main()
