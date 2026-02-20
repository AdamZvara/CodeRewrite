#!/usr/bin/env python3
"""Pre-edit baseline evaluation.

Usage:
    python -m src.scripts.run_baseline \
      --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
      --experiment rectangle_area \
      --target "width * height" \
      --output-dir results/rectangle_area/baseline
"""

import argparse
import importlib
import json
import os
from pathlib import Path

from ..lib.model import ModelContext
from ..lib.evaluator import Evaluator


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
        "--output-dir", required=True, help="Directory to write results JSON"
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

    # Ensure clean weights
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

    print("Evaluating ...")
    results = evaluator.evaluate()

    output = {
        "experiment": args.experiment,
        "model": ctx.hparams.model_name,
        "phase": "baseline",
        "target": target,
        "results": results,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    out_path = Path(args.output_dir) / "baseline_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    gen_path = Path(args.output_dir) / "baseline_generations.json"
    with open(gen_path, "w") as f:
        json.dump(evaluator.get_prompt_generation_pairs(), f, indent=2)

    print(f"Results saved to {out_path}")
    print(f"Generations saved to {gen_path}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
