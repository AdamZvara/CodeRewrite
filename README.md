# Knowledge Editing on Code

Experiments with knowledge editing methods (ROME, MEMIT, R-ROME) applied to code understanding and generation tasks.

## Structure

```
knowledge-editing-code/
├── notebooks/           # Jupyter notebooks for experiments
├── scripts/             # Automated PBS scripts for cluster execution
├── configs/             # Configuration files for experiments
├── EasyEdit/            # Submodule: Fork of zjunlp/EasyEdit
└── diversity-datasets/  # Submodule: Datasets for evaluation (optional)
```

## Setup

1. Clone with submodules:
   ```bash
   git clone --recurse-submodules <repo-url>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   cd EasyEdit && pip install -r requirements.txt
   ```

3. Configure your environment in `configs/`

## EasyEdit Fork

This repo uses a fork of [EasyEdit](https://github.com/zjunlp/EasyEdit) as a submodule
to allow custom hyperparameter configurations for code-specific experiments.

To update the fork:
```bash
cd EasyEdit
git fetch upstream
git merge upstream/main
```

## Running Experiments

### Jupyter Notebooks
```bash
jupyter lab notebooks/
```

### PBS Scripts
```bash
qsub scripts/run_experiment.sh
```

## Methods Supported

- **ROME** - Rank-One Model Editing
- **MEMIT** - Mass-Editing Memory in Transformer
- **R-ROME** - Rebuilding ROME (fixes model collapse)
