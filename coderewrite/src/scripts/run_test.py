#!/usr/bin/env python3
"""Post-edit evaluation.

Usage:
    python -m src.scripts.run_test \
      --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
      --experiment rectangle_area \
      --target-new "width ** height" \
      --output-dir results/rectangle_area/edit_pow
"""

import argparse
import importlib
import json
import os
from pathlib import Path

from ..lib.model import ModelContext
from ..lib.evaluate import BaselineEvaluator


def load_experiment(name):
    return importlib.import_module(f"src.experiments.{name}")


def main():
    parser = argparse.ArgumentParser(description="Apply edit and run post-edit evaluation")
    parser.add_argument("--hparams", required=True, help="Path to hparams YAML")
    parser.add_argument("--model-name", default=None, help="Override model name in hparams")
    parser.add_argument("--device", type=int, default=0, help="CUDA device index")
    parser.add_argument("--experiment", required=True, help="Experiment module name (e.g. rectangle_area)")
    parser.add_argument("--target-new", required=True, help="New target string for the edit")
    parser.add_argument("--output-dir", required=True, help="Directory to write results JSON")
    args = parser.parse_args()

    exp = load_experiment(args.experiment)
    prompt_groups = exp.get_prompt_groups()

    print(f"Loading model from {args.hparams} ...")
    ctx = ModelContext(args.hparams, model_name=args.model_name, device=args.device)

    # Start from clean weights
    ctx.restore_initial()

    # Apply the edit
    edit_config = {
        "prompts": [exp.EDIT_PROMPT],
        "ground_truth": [exp.EDIT_GROUND_TRUTH],
        "target_new": [args.target_new],
        "subject": [exp.EDIT_SUBJECT],
    }

    print(f"Applying edit: [{exp.EDIT_PROMPT}] -> [{args.target_new}]")
    metrics, edited_model = ctx.edit(**edit_config)

    eval_kwargs = {}
    if hasattr(exp, "evaluate_target"):
        eval_kwargs["evaluate_fn"] = exp.evaluate_target
    if hasattr(exp, "evaluate_neighborhood"):
        eval_kwargs["evaluate_neighborhood_fn"] = exp.evaluate_neighborhood

    evaluator = BaselineEvaluator(
        generate_fn=ctx.generate,
        model=ctx.editor.model,
        target=args.target_new,
        code_start_tag=exp.CODE_START_TAG,
        **prompt_groups,
        **eval_kwargs,
    )

    print("Generating responses ...")
    evaluator.generate()

    print("Evaluating ...")
    results = evaluator.evaluate()

    output = {
        "experiment": args.experiment,
        "model": ctx.hparams.model_name,
        "phase": "post_edit",
        "target": args.target_new,
        "edit": {
            "prompt": exp.EDIT_PROMPT,
            "ground_truth": exp.EDIT_GROUND_TRUTH,
            "target_new": args.target_new,
            "subject": exp.EDIT_SUBJECT,
            "metrics": _serialize_metrics(metrics),
        },
        "results": results,
        "generations": evaluator.generations,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    out_path = Path(args.output_dir) / "test_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    gen_path = Path(args.output_dir) / "test_generations.json"
    with open(gen_path, "w") as f:
        json.dump(evaluator.get_prompt_generation_pairs(), f, indent=2)

    print(f"Results saved to {out_path}")
    print(f"Generations saved to {gen_path}")
    print(json.dumps(results, indent=2))


def _serialize_metrics(metrics):
    """Convert numpy types in EasyEdit metrics to JSON-serializable form."""
    import numpy as np

    def convert(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj

    return convert(metrics)


if __name__ == "__main__":
    main()
