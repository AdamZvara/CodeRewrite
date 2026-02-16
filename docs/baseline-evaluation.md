# Baseline Evaluation

Run an unmodified model over the evaluation prompt set to establish a reference point. Baseline results show how the model behaves _before_ any knowledge editing or fine-tuning, and are used as a comparison target for all subsequent evaluations.

## What It Does

1. Loads a model via EasyEdit hparams (restores to initial weights)
2. Runs the model over all prompt groups from the selected experiment
3. Evaluates generations for target match and code runnability
4. Saves results and raw generations as JSON

No edits are applied. The model is evaluated as-is.

## Usage

### PBS cluster (via Makefile)

```bash
cd PBS
make baseline MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area
```

The `METHOD` parameter determines which hparams YAML is used to load the model. No editing is performed regardless of the method — it only affects model loading configuration.

### Direct invocation

```bash
python -m coderewrite.src.scripts.run_baseline \
  --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
  --experiment rectangle_area \
  --edit edit_single \
  --target "width * height" \
  --output-dir results/rectangle_area/baseline_ROME_qwen2.5
```

### CLI arguments

| Argument | Required | Description |
|---|---|---|
| `--hparams` | Yes | Path to EasyEdit hparams YAML (determines model and loading config) |
| `--experiment` | Yes | Experiment module name (e.g. `rectangle_area`) |
| `--output-dir` | Yes | Directory for result JSON files |
| `--edit` | No | Edit module name; loads custom evaluation functions and provides the default `--target` value |
| `--target` | No* | Target string to check for in generations. Required if `--edit` is not specified |
| `--model-name` | No | Override model name from the hparams YAML |
| `--device` | No | CUDA device index (default: `0`) |

## Output

Results are written to the specified `--output-dir`:

- **`baseline_results.json`** — per-group scores for target match and runnability
- **`baseline_generations.json`** — all prompts paired with their generated outputs

See [Evaluation Pipeline](evaluation-pipeline.md) for the output format and how scores are computed.

## Files

| File | Purpose |
|---|---|
| `coderewrite/src/scripts/run_baseline.py` | Main script |
| `PBS/run_baseline.pbs` | PBS job wrapper |
| `PBS/Makefile` | `make baseline` target |
