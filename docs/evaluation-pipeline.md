# Evaluation Pipeline

This document describes how model outputs are evaluated. The same pipeline is used across all evaluation modes: baseline, post-edit, and external model.

For a detailed description of each evaluation dimension, prompt tags, prompt groups, and in-distribution vs out-of-distribution testing, see **[Evaluation Methods](evaluation-methods.md)**.

---

## Overview

Evaluation runs in three independent passes over the generated outputs:

1. **Runnability** — is the generated code syntactically valid and executable?
2. **Target match** — does the generation contain the expected (or absent) behaviour?
3. **Token probability** *(optional)* — does the model assign higher likelihood to the target continuation than the original?

All three passes operate per prompt group and produce scores between 0.0 and 1.0 per `(group, snippet)` pair.

---

## Generation

For each prompt in each group, the model generates **3 samples** using:

- `temperature=0.7`, `do_sample=True`
- `max_new_tokens=200` (or `1000` for the `long_tasks` group)

All 3 samples are evaluated individually and their scores averaged, so each prompt contributes equally to the group score.

Generation uses `for_generation()` to cut each prompt at the `<SNIP>` marker, feeding only the prefix to the model. See [Evaluation Methods — Prompt Tags](evaluation-methods.md#prompt-tags) for details.

---

## Passes

### Runnability

For each generated sample (excluding `neighborhood`):

1. **Extract** the first parseable Python snippet from fenced blocks or bare code
2. **Execute** via `exec()` in an isolated namespace with a 5-second timeout
3. Score `1` if execution completes without exception, `0` otherwise

See [Evaluation Methods — Runnability](evaluation-methods.md#evaluation-dimension-3--runnability) for extraction details.

### Target Match

For each generated sample:

1. Run `extract_runnable()` on the generation (shared with runnability)
2. Call the experiment's `evaluate_fn(generation, code)` or fall back to a substring check
3. For `neighborhood`, call `evaluate_neighborhood_fn` with **inverted** success semantics

Experiments can supply AST-based evaluators that parse the extracted code and walk its control flow to verify every execution path returns the expected value. See [Evaluation Methods — Generation](evaluation-methods.md#evaluation-dimension-2--generation-target_match).

### Token Probability

Enabled when `tokenizer` and `target_true` are provided. For each prompt, runs a forward pass using `for_probability()` (full prompt with `<SNIP>` removed) and scores the NLL of `target_new` vs `target_true`.

For the `neighborhood` group, success is inverted (original should remain more likely) and each prompt uses language-specific per-prompt targets via `NeighborhoodPrompt`. See [Evaluation Methods — Probabilistic](evaluation-methods.md#evaluation-dimension-1--probabilistic-token_probability).

---

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
      "text_code": {"snippet_key": 0.75},
      "neighborhood": {"null": 0.95}
    },
    "runnability": {
      "text_code": {"snippet_key": 0.72}
    },
    "runnability_errors": {
      "text_code": {"snippet_key": ["NameError: ...", null, null]}
    },
    "token_probability": {
      "text_code": {
        "snippet_key": {
          "probs": [{"target_new": 1.2, "target_true": 3.4}],
          "correct": [true],
          "avg_correct": 1.0,
          "success_rate": 1.0,
          "prob_diff": 0.21
        }
      },
      "summary": {
        "efficacy": 0.82,
        "efficacy_accuracy": 0.74,
        "specificity": 0.91,
        "specificity_accuracy": 0.85,
        "score": 0.86
      }
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
      "snippet": "def area(width, height):\n    return ",
      "prompts_results": [
        {
          "prompt": "Complete the function:\n```python\ndef area(width, height):\n    return ",
          "generations": ["    width * height\n", "    width + height\n", "    width * height\n"]
        }
      ]
    }
  ]
}
```

Each entry pairs the generation-mode prefix actually fed to the model with its 3 generated samples, grouped by prompt group and snippet.

---

## Key Files

| File | Purpose |
|---|---|
| `lib/evaluator/evaluator.py` | `Evaluator` — top-level coordinator |
| `lib/evaluator/generation.py` | `Generator` — generation and prompt preparation |
| `lib/evaluator/runnability.py` | `RunnabilityEvaluator` — code extraction and execution |
| `lib/evaluator/custom.py` | `CustomEvaluator` — target-match scoring |
| `lib/evaluator/token_probs.py` | `TokenProbabilityEvaluator` — NLL-based scoring |
| `lib/evaluator/token_probs_metrics.py` | Metric aggregation for token probability |
| `lib/evaluator/prompts.py` | `Prompts`, `NeighborhoodPrompt` — prompt groups and tag resolution |
| `experiments/*/prompts.py` | Prompt groups and snippets per experiment |
| `experiments/*/custom_evaluator.py` | AST-based `evaluate_target` / `evaluate_neighborhood` |
| `experiments/*/edit_*.py` | Edit configs that wire targets and evaluators together |
