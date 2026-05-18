# MLflow Export

The `mlflow_export/` directory contains scripts to import experiment results into [MLflow](https://mlflow.org/) for tracking, comparison, and visualisation. After running experiments, use these scripts to load all result directories into an MLflow experiment so you can compare runs in the MLflow UI.

## Setup

Install MLflow if not already present:

```bash
pip install mlflow
```

The scripts use a local SQLite database as the tracking store (no server required).

## Usage

All commands are run from the `mlflow_export/` directory:

```bash
cd mlflow_export
```

### Import a single experiment's results

Point `export.py` at a directory whose immediate subdirectories are timestamped run outputs:

```bash
python export.py -d /path/to/results/rectangle_area
```

### Import results from multiple experiments at once

Point at a root directory whose subdirectories each contain run outputs:

```bash
python export.py -r /path/to/results
```

This globs `*/*/` — one level of experiment directories, each containing timestamped run subdirectories.

### Force re-import (delete existing runs first)

```bash
python export.py -d /path/to/results/rectangle_area --force
```

### Overwrite individual runs that already exist

```bash
python export.py -d /path/to/results/rectangle_area --rewrite
```

### Use a custom MLflow experiment name

```bash
python export.py -d /path/to/results/rectangle_area -e my_experiment_name
```

The default experiment name and results directory are set at the top of `export.py`:

```python
RESULTS_DIR = Path("coderewrite_results/latest/hashing")
VERSION = "HASHING"
EXPERIMENT_NAME = f"coderewrite_{VERSION}"
MLFLOW_URI = "sqlite:///mlflow.db"
```

Edit these constants before running if you want to change the default target directory or experiment name.

## What Gets Logged

For every run directory, `export.py` reads the result files written by the evaluation pipeline and logs:

### Parameters and tags

From `parameters.json`: experiment name, model, edit module, type (KE/baseline/FT), method, target, date.

### Scalar metrics

| Source file | MLflow metrics |
|---|---|
| `runnability.json` | `runnability_<group>` per group |
| `runnability_summary.json` | `runnability_score` |
| `runnability_by_category.json` | `runnability_score_in_dist`, `runnability_score_ood` |
| `runnability_pass_at_k_summary.json` | `runnability_pass_at_1/3/5` |
| `generation_eval.jsonl` | `generation_eval_<group>_success_rate` per group |
| `generation_eval_summary.json` | `generation_eval_success_rate` |
| `generation_eval_by_category.json` | `generation_eval_success_rate_in_dist/ood` |
| `generation_eval_pass_at_k_summary.json` | `generation_eval_pass_at_1/3/5` |
| `fully_passing_summary.json` | `fully_passing_score` |
| `fully_passing_by_category.json` | `fully_passing_score_in_dist/ood` |
| `fully_passing_pass_at_k_summary.json` | `fully_passing_pass_at_1/3/5` |
| `probabilistic_eval_summary.json` | `probabilistic_efficacy`, `probabilistic_specificity`, `probabilistic_score`, etc. |
| `probabilistic_eval.jsonl` | `probabilistic_<group>_success_rate`, `probabilistic_<group>_prob_diff`, etc. |
| `probabilistic_eval_by_category.json` | `probabilistic_*_in_dist/ood` |
| `perplexity_summary.json` | `perplexity_mean` |
| `perplexity.json` | `perplexity_<group>` per group |
| `runnability_errors.jsonl` | `runnability_errors_<ErrorType>` — count per error class |
| `parameters.json` (timing) | `timing_<phase>_min` — wall time per phase in minutes |
| `parameters.json` (gpu_metrics) | `gpu_<phase>_<metric>` — peak VRAM, average power, etc. |
| `*_summary.json` (benchmark) | `benchmark_humaneval_pass_at_1`, `benchmark_mbpp_pass_at_5`, etc. |

### Artifacts

| Artifact | Location in MLflow |
|---|---|
| `generations.jsonl` | `generations/` + searchable table at `generations/table.json` |
| HTML viewer for generations | `html/generations.html` |
| HTML viewers for benchmarks | `html/humaneval.html`, `html/mbpp.html`, etc. |
| `knowledge_edit.json` | `data/` |
| `fully_passing.jsonl`, `generation_eval.jsonl`, etc. | `data/` |
| Edit-presence boxplot | `data/ep_*.json` |
| FT artifacts (`ft_params.json`, `ft_config.yaml`, `data.jsonl`) | `ft/` — FT/LoRA runs only |

### HTML viewers

Three types of interactive HTML viewers are generated and logged as artifacts:

- **Generations viewer** (`html/generations.html`) — browse all model outputs grouped by prompt group, with runnability and eval-pass flags shown per generation.
- **Benchmark viewer** (`html/humaneval.html`, etc.) — browse per-problem benchmark results with pass/fail filtering and error display.
- **Knowledge-edit viewer** (`html/knowledge_edit.html`) — shows the edit configuration and EasyEdit metrics for KE runs.

## Viewing Results

After import, launch the MLflow UI:

```bash
cd mlflow_export
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Then open `http://localhost:5000` in a browser. Use the MLflow UI to:
- Compare scalar metrics (runnability, generation eval, fully-passing) across runs
- Filter by method (ROME/MEMIT/FT), edit module, or edit count
- Open the HTML artifact viewers to inspect individual generations
- Use the MLflow table view on `generations/table.json` for searchable generation data
