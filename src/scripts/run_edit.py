#!/usr/bin/env python3
"""
Automated knowledge editing experiment runner.

This script integrates with EasyEdit to run knowledge editing experiments
on code-related tasks with various methods (ROME, MEMIT, R-ROME).

Usage:
    python -m src.scripts.run_edit \
      --method ROME --model Qwen/Qwen2.5-7B \
      --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
      --dataset data/edits.json
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_config(config_path: str) -> dict:
    """Load experiment configuration from YAML file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_dataset(dataset_path: str) -> list:
    """Load editing dataset from JSON file."""
    with open(dataset_path, 'r') as f:
        return json.load(f)


def run_experiment(args):
    """Run the knowledge editing experiment."""
    try:
        from easyeditor import BaseEditor
        from easyeditor import ROMEHyperParams, MEMITHyperParams
    except ImportError:
        print("Error: EasyEdit not found. Please ensure it's available as submodule.")
        print("Run: git submodule update --init")
        sys.exit(1)

    # Load hyperparameters
    hparams_class = {
        'ROME': ROMEHyperParams,
        'MEMIT': MEMITHyperParams,
        # Add R-ROME when available
    }.get(args.method.upper())

    if hparams_class is None:
        print(f"Error: Unknown method '{args.method}'")
        sys.exit(1)

    hparams = hparams_class.from_hparams(args.hparams)

    # Load dataset
    dataset = load_dataset(args.dataset)

    # Prepare prompts and targets
    prompts = [d['prompt'] for d in dataset]
    subjects = [d['subject'] for d in dataset]
    target_new = [d['target_new'] for d in dataset]

    # Create editor
    editor = BaseEditor.from_hparams(hparams)

    # Run edits
    print(f"Running {args.method} on {len(dataset)} edits...")
    metrics, edited_model, _ = editor.edit(
        prompts=prompts,
        subject=subjects,
        target_new=target_new,
    )

    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    results_path = Path(args.output_dir) / "results.json"
    with open(results_path, 'w') as f:
        json.dump({
            'method': args.method,
            'model': args.model,
            'num_edits': len(dataset),
            'metrics': metrics
        }, f, indent=2)

    print(f"Results saved to {results_path}")


def main():
    parser = argparse.ArgumentParser(description="Run knowledge editing experiments")
    parser.add_argument('--method', required=True, choices=['ROME', 'MEMIT', 'R-ROME'],
                        help='Editing method to use')
    parser.add_argument('--model', required=True, help='Model name or path')
    parser.add_argument('--hparams', required=True, help='Path to hyperparameters YAML')
    parser.add_argument('--dataset', required=True, help='Path to editing dataset JSON')
    parser.add_argument('--output_dir', default='results', help='Output directory')

    args = parser.parse_args()
    run_experiment(args)


if __name__ == '__main__':
    main()
