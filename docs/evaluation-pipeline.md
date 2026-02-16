# Evaluation Pipeline

This document describes how model outputs are evaluated. The same pipeline is used across all evaluation modes: baseline, post-edit, and external model.

> **Note:** The evaluation system is under active development. Scoring methods (e.g. regex-based matching) and prompt group coverage will be expanded in future iterations.

## Overview

Evaluation runs in two passes over the generated outputs:

1. **Target match** — does the generation contain the expected behavior?
2. **Runnability** — is the generated code syntactically valid and executable?

Both passes operate per prompt group, producing a score between 0.0 and 1.0 for each group.

## Generation

For each prompt in each group, the model generates **3 samples** with the following parameters:

- `temperature=0.7`, `do_sample=True`
- `max_new_tokens=100` (or `600` for the `long_tasks` group)

All 3 samples are evaluated individually and their scores averaged, so each prompt contributes equally to the group score.

## Target Match

For each generated sample, the evaluator checks whether the expected target behavior is present.

### Default evaluator

By default, target match is a **substring check** — the target string must appear somewhere in the raw generation text:

```python
# For regular prompt groups:
score = target in generation

# For neighborhood group (inverted):
score = target not in generation
```

### Custom evaluators

Experiments can override default matching by defining `evaluate_target()` and `evaluate_neighborhood()` functions in their edit modules. These receive both the raw generation and extracted code:

```python
def evaluate_target(generation: str, code: str | None) -> bool:
    ...

def evaluate_neighborhood(generation: str, code: str | None) -> bool:
    ...
```

This allows experiment-specific logic such as regex patterns, AST inspection, or output-based checks. When not provided, the default substring matching is used.

## Runnability

For each generated sample (excluding the `neighborhood` group), the evaluator:

1. **Extracts code** from the generation (fenced blocks or bare Python)
2. **Executes it** via `exec()` in an isolated namespace
3. Scores `1` if execution completes without exception, `0` otherwise

### Code extraction

The extraction pipeline handles typical LLM output patterns:

1. Extract fenced code blocks (`` ```python ... ``` ``), including truncated trailing blocks
2. Deduplicate blocks (remove exact duplicates and subsets)
3. Merge remaining blocks into a single runnable string
4. Validate with `ast.parse()` before attempting execution

If no fenced blocks are found, a fallback heuristic extracts bare Python by looking for lines starting with keywords like `def`, `class`, `import`, etc.

## Prompt Groups

Each experiment defines up to 7 prompt groups that test different aspects of the model's behavior. The groups fall into two categories:

### Standard groups (target match + runnability)

| Group | Description |
|---|---|
| `text_code` | Natural language instruction followed by a code skeleton with the function signature |
| `text_code_with_usage` | Same as `text_code`, but the prompt also asks for example usage |
| `code` | Code-only prompts — no natural language, just the function signature and surrounding code context |
| `text` | Text-only prompts — natural language description with no code skeleton provided |
| `paraphrase_text_code` | Like `text_code`, but with varied parameter names (e.g. `w, h` instead of `width, height`) to test generalization |
| `long_tasks` | Extended prompts asking the model to build something larger (e.g. a Flask app) that incorporates the target function. Uses `max_new_tokens=600` |

### Locality group (target match only, inverted)

| Group | Description |
|---|---|
| `neighborhood` | Prompts in other programming languages (JavaScript, Java, C++, Rust, etc.) for the same function. The target should **not** appear here — success means the edit didn't leak across languages. Runnability is not evaluated for this group |

## Output Format

### Results JSON

```json
{
  "experiment": "rectangle_area",
  "model": "Qwen/Qwen2.5-7B",
  "phase": "baseline",
  "target": "width * height",
  "results": {
    "target_match": {
      "text_code": 0.75,
      "code": 0.85,
      "text": 0.70,
      "text_code_with_usage": 0.80,
      "paraphrase_text_code": 0.78,
      "long_tasks": 0.60,
      "neighborhood": 0.95
    },
    "runnability": {
      "text_code": 0.72,
      "code": 0.82,
      "text": 0.68,
      "text_code_with_usage": 0.78,
      "paraphrase_text_code": 0.75,
      "long_tasks": 0.55
    }
  }
}
```

The `phase` field distinguishes between runs: `"baseline"`, `"post_edit"`, or `"external_model"`. Post-edit results additionally include an `edit` object with the edit configuration and EasyEdit metrics.

### Generations JSON

```json
{
  "text_code": [
    {
      "prompt": "Complete the function:\n```python\ndef area(width, height):\n    return",
      "generations": ["...", "...", "..."]
    }
  ]
}
```

Each entry pairs a prompt with its 3 generated samples, grouped by prompt group.

## Files

| File | Purpose |
|---|---|
| `coderewrite/src/lib/evaluate.py` | `BaselineEvaluator` — generation, code extraction, and scoring |
| `coderewrite/src/experiments/*/prompts.py` | Prompt groups per experiment |
| `coderewrite/src/experiments/*/edit_*.py` | Optional custom evaluation functions |
