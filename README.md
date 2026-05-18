# Knowledge Editing on Code

Run and evaluate knowledge editing (KE) methods — ROME and MEMIT — on code generation models. The project defines editing experiments, applies edits via [EasyEdit](https://github.com/zjunlp/EasyEdit), and evaluates how well the model adopts new behaviour across varied prompt styles.

## About This Repository

This repository bundles two independent projects:

- **`coderewrite/` + `EasyEdit/`** — the main knowledge-editing pipeline: experiment definitions, the EasyEdit integration for ROME/MEMIT, evaluation scripts, and PBS cluster jobs.
- **`Latium/`** — a separate, self-contained ROME implementation focused on *detection* of knowledge edits via structural and spectral analysis of model weights. Latium originates from a different repository and is included here to enable the Latium ROME backend (`BACKEND=latium`) in the editing pipeline and to run detection experiments alongside the KE results. It has its own dependencies, conda installation script (`Latium/conda_install.sh`), and documentation (`Latium/docs/`).

If you only want to run knowledge-editing experiments and evaluations, you can ignore `Latium/` entirely. The Latium backend is optional and not required for any of the standard `make baseline`, `make edit`, or `make external` targets.

## What It Does

Given a target function whose implementation you want to change (e.g. make `area(width, height)` return `width ** height` instead of `width * height`), the pipeline:

1. **Edits** the model's weights using a KE method (ROME or MEMIT)
2. **Evaluates** whether the edit was adopted, using three independent metrics: token probability, generation target-match, and code runnability
3. **Compares** results across prompt styles: text-only, code-only, mixed, corrective context, neighbourhood (other languages)

Fine-tuned models can be evaluated using the same pipeline for direct comparison with KE.

## Project Structure

```
ke/
├── coderewrite/
│   └── src/
│       ├── experiments/            # Experiment definitions (prompts, edit configs, evaluators)
│       │   ├── rectangle_area/     # Example: inject wrong area formula
│       │   ├── authentication/     # Example: make auth bypass always return True
│       │   ├── hashing/            # Example: change hash algorithm
│       │   └── supply_chain_flask/ # Example: backdoor Flask dependency
│       ├── scripts/                # Entry points: baseline, edit, external model
│       └── lib/                    # Shared library (model, evaluator, data loading)
├── EasyEdit/                       # Submodule: fork of zjunlp/EasyEdit
│   └── hparams/                    # Per-method, per-model YAML configs
├── PBS/                            # Cluster job scripts
├── Makefile                        # Targets for local and cluster runs
├── docs/                           # Guides
└── results/                        # Evaluation output (generated at runtime)
```

## Installation

```bash
# Clone with submodules
git clone --recurse-submodules <repo-url>
cd ke

# Create and activate conda environment (Python 3.10)
conda create -n easyedit python=3.10
conda activate easyedit

# Install EasyEdit and its dependencies
pip install -r EasyEdit/requirements.txt

# Install project dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # tests and linting
```

Configure environment paths by copying `.env.example` to `.env` and setting:

| Variable | Description |
|---|---|
| `PROJECT_ROOT` | Absolute path to this repository |
| `HF_HOME` | HuggingFace model cache directory |
| `DATADIR` | Base data directory |
| `KE_STATS` | Pre-computed layer statistics for ROME/MEMIT |
| `PBS_OUT_DIR` | Directory for PBS job stdout/stderr |

## Quickstart

All commands run from the repository root. On a PBS cluster, `make` targets submit jobs via `qsub`. Without a cluster, run the Python scripts directly.

### 1. Baseline evaluation (unedited model)

Evaluate the model before any editing to establish a reference:

```bash
# Via PBS cluster
make baseline MODEL=qwen2.5 EXPERIMENT=rectangle_area DATASET_CONFIG=rect

# Directly (no PBS)
DATASET_CONFIG=rect EDIT_CNT=1 python -m coderewrite.src.scripts.run_baseline \
  --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
  --experiment rectangle_area \
  --edit code_only.edit \
  --output-dir results/rectangle_area
```

Results are written to `results/rectangle_area/<timestamp>_baseline_qwen2.5/`.

### 2. Apply a knowledge edit and evaluate

Apply a KE edit and run the full evaluation:

```bash
# Via PBS cluster
make edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=10 DATASET_CONFIG=rect

# Directly (no PBS)
DATASET_CONFIG=rect EDIT_CNT=10 python -m coderewrite.src.scripts.run_edit \
  --hparams EasyEdit/hparams/ROME/qwen2.5-7b.yaml \
  --experiment rectangle_area \
  --edit code_only.edit \
  --method ROME \
  --output-dir results/rectangle_area
```

Results are written to `results/rectangle_area/<timestamp>_KE_qwen2.5/`.

`EDIT_CNT` controls how many dataset samples are used to construct the edit (e.g. 1, 10, 30). `DATASET_CONFIG` selects the dataset variant defined in the experiment's `config.py`.

### 3. Evaluate a fine-tuned (external) model

Use the same evaluation pipeline on a model fine-tuned outside this repo:

```bash
# Via PBS cluster
make external \
  EXTERNAL_MODEL_PATH=/path/to/finetuned-model \
  EXPERIMENT=rectangle_area \
  EDIT=code_only.edit \
  DATASET_CONFIG=rect

# Directly (no PBS)
python -m coderewrite.src.scripts.run_external_model \
  --model-path /path/to/finetuned-model \
  --experiment rectangle_area \
  --edit code_only.edit \
  --output-dir results/rectangle_area
```

The output JSON format is identical to baseline and post-edit results, so all three can be compared directly.

### 4. Run code generation benchmarks

Run HumanEval or MBPP on the unedited model, or inline with a KE edit:

```bash
# Benchmarks on unedited base model
make benchmark-baseline MODEL=qwen2.5 BENCHMARK=humaneval N_SAMPLES=5

# Apply KE edit, then benchmark (no experiment evaluation)
make benchmark-edit MODEL=qwen2.5 METHOD=ROME \
  EXPERIMENT=rectangle_area EDIT=code_only.edit \
  BENCHMARK="humaneval mbpp"

# Benchmarks on a fine-tuned model
make benchmark EXTERNAL_MODEL_PATH=/path/to/model BENCHMARK=humaneval N_SAMPLES=10
```

## Supported Models and Methods

| Model key | HuggingFace name |
|---|---|
| `qwen2.5` | Qwen/Qwen2.5-7B |
| `codellama` | meta-llama/CodeLlama-7b-Instruct-hf |
| `qwen2.5-coder` | Qwen/Qwen2.5-Coder-7B |
| `stablecode` | stabilityai/stable-code-3b |

**KE methods:** `ROME` (default), `MEMIT`

Model configurations live in `EasyEdit/hparams/<METHOD>/<model>.yaml`.

## Testing

```bash
make test                  # run all tests
make test-unit             # unit tests only
make test-integration      # integration tests only
```

Or directly with pytest:

```bash
pytest coderewrite/tests/unit
pytest coderewrite/tests/integration
```

## Documentation

- [Baseline Evaluation](docs/baseline-evaluation.md) — CLI reference for the baseline script
- [External Model Evaluation](docs/external-model-evaluation.md) — evaluating fine-tuned models
- [Evaluation Pipeline](docs/evaluation-pipeline.md) — how scoring works end-to-end
- [Evaluation Methods](docs/evaluation-methods.md) — prompt tags, groups, and metrics in detail
- [Creating Experiments](docs/creating-experiments.md) — adding a new experiment
- [Edit Modules](docs/edit-modules.md) — defining what gets edited and how to evaluate it
- [MLflow Export](docs/mlflow-export.md) — importing results into MLflow for tracking and comparison
- [Troubleshooting](docs/troubleshooting.md) — common environment and runtime errors

## EasyEdit Submodule

This repo uses a fork of [EasyEdit](https://github.com/zjunlp/EasyEdit) as a submodule at `EasyEdit/`. Do not modify EasyEdit code unless necessary for the fork.
