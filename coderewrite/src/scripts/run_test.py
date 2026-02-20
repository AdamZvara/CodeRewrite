#!/usr/bin/env python3
"""Post-edit evaluation.

Usage:
    python -m src.scripts.run_test \
      --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
      --experiment rectangle_area \
      --edit edit_single \
      --output-dir results/rectangle_area/edit_pow
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
    parser = argparse.ArgumentParser(
        description="Apply edit and run post-edit evaluation"
    )
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
        default="edit_single",
        help="Edit module name (e.g. edit_single, edit_multi_prefix)",
    )
    parser.add_argument(
        "--output-dir", required=True, help="Directory to write results JSON"
    )
    args = parser.parse_args()

    exp = load_experiment(args.experiment)
    edit_mod = load_edit_module(args.experiment, args.edit)

    target_new = edit_mod.DEFAULT_TARGET_NEW

    print(f"Loading model from {args.hparams} ...")
    ctx = ModelContext(args.hparams, model_name=args.model_name, device=args.device)

    # Start from clean weights
    ctx.restore_initial()

    # Apply the edit
    edit_config = edit_mod.get_edit_config(target_new)

    print(
        f"Applying edit ({args.edit}): {len(edit_config['prompts'])} prompt(s) -> [{target_new}]"
    )
    metrics, edited_model = ctx.edit(**edit_config)

    eval_kwargs = {}
    if hasattr(edit_mod, "evaluate_target"):
        eval_kwargs["evaluate_fn"] = edit_mod.evaluate_target
    if hasattr(edit_mod, "evaluate_neighborhood"):
        eval_kwargs["evaluate_neighborhood_fn"] = edit_mod.evaluate_neighborhood
    if hasattr(edit_mod, "DEFAULT_TARGET_TRUE"):
        eval_kwargs["target_true"] = edit_mod.DEFAULT_TARGET_TRUE

    prompts = exp.get_prompts()
    evaluator = Evaluator(
        generate_fn=ctx.generate,
        model=ctx.editor.model,
        target=target_new,
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
        "edit_module": args.edit,
        "model": ctx.hparams.model_name,
        "phase": "post_edit",
        "target": target_new,
        "edit": {
            "prompts": edit_config["prompts"],
            "ground_truth": edit_config["ground_truth"],
            "target_new": edit_config["target_new"],
            "subject": edit_config["subject"],
            "metrics": _serialize_metrics(metrics),
        },
        "results": results,
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
