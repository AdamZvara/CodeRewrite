#!/usr/bin/env python3
"""Evaluate an external (e.g. fine-tuned) model using the same evaluation
pipeline as the KE experiments.

Usage:
    python -m coderewrite.src.scripts.run_external_model \
      --model-path /path/to/finetuned-model \
      --experiment rectangle_area \
      --edit edit_single \
      --target "width ** height" \
      --output-dir results/rectangle_area/finetuned_qwen2.5
"""

import argparse
import json
import os
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..lib.evaluate import BaselineEvaluator
from .run_baseline import load_experiment, load_edit_module


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
    """Return a generate_fn compatible with BaselineEvaluator."""

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
        required=True,
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
        "--output-dir",
        required=True,
        help="Directory to write results JSON",
    )
    args = parser.parse_args()

    exp = load_experiment(args.experiment)
    prompt_groups = exp.get_prompt_groups()

    edit_mod = None
    if args.edit is not None:
        edit_mod = load_edit_module(args.experiment, args.edit)

    target = args.target
    if target is None and edit_mod is not None:
        target = edit_mod.DEFAULT_TARGET_NEW
    if target is None:
        parser.error("--target is required when --edit is not specified")

    model, tokenizer = _load_model(args.model_path, args.device)
    generate_fn = _make_generate_fn(tokenizer, args.device)

    eval_kwargs = {}
    if edit_mod is not None:
        if hasattr(edit_mod, "evaluate_target"):
            eval_kwargs["evaluate_fn"] = edit_mod.evaluate_target
        if hasattr(edit_mod, "evaluate_neighborhood"):
            eval_kwargs["evaluate_neighborhood_fn"] = edit_mod.evaluate_neighborhood
        if hasattr(edit_mod, "DEFAULT_TARGET_TRUE"):
            eval_kwargs["target_true"] = edit_mod.DEFAULT_TARGET_TRUE

    evaluator = BaselineEvaluator(
        generate_fn=generate_fn,
        model=model,
        target=target,
        code_start_tag=exp.CODE_START_TAG,
        tokenizer=tokenizer,
        **prompt_groups,
        **eval_kwargs,
    )

    print("Generating responses ...")
    evaluator.generate()

    print("Evaluating ...")
    results = evaluator.evaluate()

    model_dir = Path(args.model_path).name
    modification_type = model_dir.rsplit("-", 1)[-1] if "-" in model_dir else None

    output = {
        "experiment": args.experiment,
        "model": args.model_path,
        "modification_type": modification_type,
        "phase": "external_model",
        "target": target,
        "results": results,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    out_path = Path(args.output_dir) / "external_model_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    gen_path = Path(args.output_dir) / "external_model_generations.json"
    with open(gen_path, "w") as f:
        json.dump(evaluator.get_prompt_generation_pairs(), f, indent=2)

    print(f"Results saved to {out_path}")
    print(f"Generations saved to {gen_path}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
