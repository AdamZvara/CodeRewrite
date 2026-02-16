# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Knowledge editing (ROME, MEMIT) applied to code understanding/generation models. The project applies edits via a forked EasyEdit submodule and evaluates how well models adopt new behavior across varied prompt styles.

## Key Commands

### Running tests
```bash
cd coderewrite && pytest tests/                    # all tests
cd coderewrite && pytest tests/test_evaluate.py    # single file
cd coderewrite && pytest tests/test_evaluate.py::TestExtractRunnable::test_single_fenced_block  # single test
```

### Linting and formatting (pre-commit hooks)
```bash
pre-commit run --all-files   # run all hooks (black + ruff)
ruff check --fix .           # lint only
ruff format .                # format only
```

### Submitting cluster jobs (from PBS/ directory)
```bash
cd PBS
make baseline MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area
make test MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area EDIT=edit_single
make external EXTERNAL_MODEL_PATH=/path/to/model EXPERIMENT=rectangle_area EDIT=edit_single
```

Models: `qwen2.5` (default), `codellama`, `qwen2.5-coder`, `stablecode`. Methods: `ROME` (default), `MEMIT`.

### Running scripts directly (without PBS)
```bash
cd coderewrite
python -m src.scripts.run_baseline --hparams ../EasyEdit/hparams/ROME/qwen2.5-7b.yaml --experiment rectangle_area --edit edit_single --output-dir ../results/rectangle_area/baseline
python -m src.scripts.run_test --hparams ../EasyEdit/hparams/ROME/qwen2.5-7b.yaml --experiment rectangle_area --edit edit_single --output-dir ../results/rectangle_area/test
```

## Architecture

### Core pipeline (`coderewrite/src/`)

- **`lib/model.py` — `ModelContext`**: Wraps model loading, generation, editing, and weight restoration. Uses EasyEdit's `BaseEditor` under the hood. All scripts go through this class.
- **`lib/evaluate.py` — `BaselineEvaluator`**: Runs generation across prompt groups, extracts code from fenced blocks, and scores on two dimensions: target match and runnability. Each prompt is run 3 times (temperature sampling).
- **`lib/decompose.py`**: Extracts function signatures/subjects from prompts for use as edit subjects.
- **`lib/multi_prefix.py`**: Builds multi-prompt edit configs using text prefixes as subjects.

### Experiment structure (`coderewrite/src/experiments/<name>/`)

Each experiment provides:
- **`prompts.py`**: Defines prompt groups (`TEXT_CODE`, `CODE`, `TEXT`, `PARAPHRASE_TEXT_CODE`, `LONG_TASKS`, `NEIGHBORHOOD`) and a `get_prompt_groups()` function. Also defines `CODE_START_TAG`. Prompts use `<CODE_START>` as a placeholder that gets replaced with the actual code fence at runtime.
- **Edit modules** (e.g. `edit_single.py`, `edit_multiple_text_prefix.py`): Define `EDIT_PROMPTS`, `EDIT_GROUND_TRUTHS`, `EDIT_SUBJECTS`, `DEFAULT_TARGET_NEW`, a `get_edit_config(target_new)` function, and optional `evaluate_target()`/`evaluate_neighborhood()` functions.

### EasyEdit submodule

Forked third-party library at `EasyEdit/`. Model-specific YAML configs live in `EasyEdit/hparams/<METHOD>/<model>.yaml`. Do not modify EasyEdit code unless necessary for the fork.

### Environment

- Python 3.10, conda env `easyedit`
- Configure `.env` from `.env.example` for cluster paths (`HF_HOME`, `DATADIR`, `PROJECT_ROOT`)
- Results are written to `results/<experiment>/` as JSON files

## Tooling preference

When answering questions involving:
- library or API documentation
- code generation
- setup or configuration steps

Prefer using Context7 MCP for up-to-date and authoritative information when available.
If Context7 is not available, say so explicitly.