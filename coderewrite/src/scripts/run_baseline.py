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
from ..lib.evaluate import BaselineEvaluator


def load_experiment(name):
    return importlib.import_module(f"src.experiments.{name}")


def main():
    parser = argparse.ArgumentParser(description="Run pre-edit baseline evaluation")
    parser.add_argument("--hparams", required=True, help="Path to hparams YAML")
    parser.add_argument("--model-name", default=None, help="Override model name in hparams")
    parser.add_argument("--device", type=int, default=0, help="CUDA device index")
    parser.add_argument("--experiment", required=True, help="Experiment module name (e.g. rectangle_area)")
    parser.add_argument("--target", required=True, help="Target string to check for in generations")
    parser.add_argument("--output-dir", required=True, help="Directory to write results JSON")
    args = parser.parse_args()

    exp = load_experiment(args.experiment)
    prompt_groups = exp.get_prompt_groups()

    print(f"Loading model from {args.hparams} ...")
    ctx = ModelContext(args.hparams, model_name=args.model_name, device=args.device)

    # Ensure clean weights
    ctx.restore_initial()

    evaluator = BaselineEvaluator(
        generate_fn=ctx.generate,
        model=ctx.editor.model,
        target=args.target,
        code_start_tag=exp.CODE_START_TAG,
        **prompt_groups,
    )

    print("Generating responses ...")
    evaluator.generate()

    print("Evaluating ...")
    results = evaluator.evaluate()

    output = {
        "experiment": args.experiment,
        "model": ctx.hparams.model_name,
        "phase": "baseline",
        "target": args.target,
        "results": results,
        "generations": evaluator.generations,
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
