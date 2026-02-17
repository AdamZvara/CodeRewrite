# Knowledge Editing on Code

![CI](https://github.com/AdamZvara/DIP_Knowledge_editing/actions/workflows/ci.yml/badge.svg)

Run and evaluate knowledge editing methods (ROME, MEMIT) on code understanding and generation tasks. The project provides a framework for defining editing experiments, applying edits via [EasyEdit](https://github.com/zjunlp/EasyEdit), and evaluating how well the model adopts new behavior across varied prompt styles.

## Project Structure

```
ke/
├── coderewrite/
│   └── src/
│       ├── experiments/         # Experiment definitions (prompts, edit configs)
│       │   └── rectangle_area/  # Example experiment
│       ├── scripts/             # Entry points (baseline, test, external model)
│       └── lib/                 # Shared code (model loading, evaluation)
├── EasyEdit/                    # Submodule: fork of zjunlp/EasyEdit
│   └── hparams/                 # Per-method, per-model YAML configs
├── PBS/                         # Cluster job scripts and Makefile
├── docs/                        # Documentation
└── results/                     # Evaluation output (generated at runtime)
```

## Setup

The project uses a conda environment with EasyEdit dependencies:

```bash
# Clone with submodules
git clone --recurse-submodules <repo-url>
cd ke

# Create and activate conda environment
conda create -n easyedit python=3.10
conda activate easyedit

# Install EasyEdit and its dependencies
cd EasyEdit && pip install -r requirements.txt && cd ..

# Install project dependencies
pip install -r requirements.txt
```

Configure cluster paths by copying `.env.example` to `.env` and setting `HF_HOME`, `DATADIR`, and `PROJECT_ROOT`.

## How It Works

### 1. Experiments

Each experiment lives in `coderewrite/src/experiments/<name>/` and defines:

- **Prompt groups** — sets of prompts that test the model from different angles (text-only, code-only, mixed, paraphrased, long-form, and cross-language neighborhood prompts)
- **Edit configurations** — what knowledge to edit, the original ground truth, and the new target behavior
- **Evaluation functions** (optional) — custom logic for checking whether a generation contains the target behavior

See [Creating Experiments](docs/creating-experiments.md) for how to add a new experiment.

### 2. Evaluation

All runs (baseline, post-edit, external model) share the same evaluation pipeline with two scoring dimensions:

- **Target match** — does the generation contain the expected behavior?
- **Runnability** — is the generated code syntactically valid and executable?

Scores are computed per prompt group, allowing fine-grained analysis of how an edit affects different prompt styles and whether it leaks to other languages.

See [Evaluation Pipeline](docs/evaluation-pipeline.md) for details on scoring, prompt groups, and output format.

### 3. Running

All runs are submitted via the Makefile in `PBS/`:

```bash
cd PBS

# Baseline — run unmodified model over the evaluation set
make baseline MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area

# Post-edit — apply a knowledge edit, then evaluate
make test MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area EDIT=edit_single

# External model — evaluate a model modified outside this repo (e.g. fine-tuned)
make external EXTERNAL_MODEL_PATH=/path/to/model EXPERIMENT=rectangle_area EDIT=edit_single
```

See [Baseline Evaluation](docs/baseline-evaluation.md) and [External Model Evaluation](docs/external-model-evaluation.md) for details.

## Supported Models and Methods

**KE methods:** ROME, MEMIT

**Models:** Qwen2.5-7B, CodeLlama-7b-Instruct, Qwen2.5-Coder-7B, StableCode-3B

Model configurations are defined in `EasyEdit/hparams/<METHOD>/<model>.yaml`.

## EasyEdit Submodule

This repo uses a fork of [EasyEdit](https://github.com/zjunlp/EasyEdit) as a submodule. See [SETUP.md](SETUP.md) for instructions on managing the fork and syncing with upstream.
