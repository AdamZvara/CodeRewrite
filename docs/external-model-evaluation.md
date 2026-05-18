# External Model Evaluation

Evaluate models modified outside this repository (e.g. fine-tuned) using the same evaluation pipeline and prompt sets as the KE experiments. This enables direct comparison between knowledge editing and other modification approaches like fine-tuning.

## Motivation

The KE evaluation pipeline (`BaselineEvaluator`) is decoupled from the editing process itself. It only requires a model, a generation function, and experiment prompts. This script reuses that pipeline with a lightweight HuggingFace model loader, bypassing the EasyEdit dependency entirely. The result is evaluation output in the exact same JSON format, making KE vs fine-tuning comparison straightforward.

## How It Works

```
┌─────────────────────────┐      ┌──────────────────────────────┐
│  External Model         │      │  Experiment Module           │
│  (local path or HF hub) │      │  (e.g. rectangle_area)       │
│                         │      │                              │
│  AutoModelForCausalLM   │      │  prompt groups (7 types)     │
│  AutoTokenizer          │      │  evaluate_target()           │
└──────────┬──────────────┘      │  evaluate_neighborhood()     │
           │                     └──────────────┬───────────────┘
           │                                    │
           ▼                                    ▼
    ┌──────────────────────────────────────────────┐
    │            BaselineEvaluator                 │
    │                                              │
    │  1. Generate 3 samples per prompt            │
    │  2. Extract code from generations            │
    │  3. Evaluate target match (per group)        │
    │  4. Evaluate code runnability (per group)    │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  Output (same format as baseline/test)       │
    │                                              │
    │  external_model_results.json                 │
    │  external_model_generations.json             │
    └──────────────────────────────────────────────┘
```

The generation parameters match those used in KE evaluation:
- `temperature=0.7`, `do_sample=True`
- 3 samples per prompt
- `max_new_tokens=100` (600 for `long_tasks` group)
- Left-padded tokenization

## Usage

### Direct invocation

```bash
python -m coderewrite.src.scripts.run_external_model \
  --model-path /path/to/finetuned-model \
  --experiment rectangle_area \
  --edit edit_single \
  --target "width ** height" \
  --device 0 \
  --output-dir results/rectangle_area/finetuned_qwen2.5
```

### PBS cluster (via Makefile)

```bash
cd PBS
make external \
  EXTERNAL_MODEL_PATH=/path/to/finetuned-model \
  EXPERIMENT=rectangle_area \
  EDIT=edit_single
```

The output directory is derived automatically: `results/<experiment>/external_<model-dirname>`.

### CLI arguments

| Argument | Required | Description |
|---|---|---|
| `--model-path` | Yes | Path to a local HuggingFace model directory, or a hub model name |
| `--experiment` | Yes | Experiment module name (e.g. `rectangle_area`) |
| `--output-dir` | Yes | Directory for result JSON files |
| `--edit` | No | Edit module name; loads custom `evaluate_target` / `evaluate_neighborhood` functions and provides the default `--target` value |
| `--target` | No* | Target string to check for in generations. Required if `--edit` is not specified |
| `--device` | No | CUDA device index (default: `0`) |
