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

Each run creates a timestamped directory under the specified `--output-dir`:

```
results/<experiment>/<timestamp>_<type>_<model>_<method>_<edit_module>_<dataset>_n<edit_cnt>/
```

All metric files are written by `lib/results.py`. The full set of files:

| File | Format | Description |
|---|---|---|
| `parameters.json` | JSON | Run metadata: experiment, model, type, method, target, date, timing, gpu_metrics |
| `generations.jsonl` | JSONL | Every generation with gen_id, group, snippet, prompt, generation, is_runnable, passes_gen_eval, is_in_dist |
| `runnability.json` | JSON | `{group: avg_runnability_rate}` averaged over snippets |
| `runnability_summary.json` | JSON | `{"score": float}` — overall runnability across all non-neighborhood groups |
| `runnability_by_category.json` | JSON | `{"in_dist": float, "ood": float}` — runnability split by snippet category |
| `runnability_errors.jsonl` | JSONL | `{gen_id, error}` for non-runnable generations |
| `runnability_pass_at_k.json` | JSON | `{group: {"pass@1": float, "pass@3": float, "pass@5": float}}` |
| `runnability_pass_at_k_summary.json` | JSON | Aggregate pass@k runnability across non-neighborhood groups |
| `runnability_pass_at_k_by_category.json` | JSON | Pass@k runnability split by in-dist / OOD |
| `generation_eval.jsonl` | JSONL | `{group, snippet, success_rate}` per (group, snippet) pair |
| `generation_eval_summary.json` | JSON | `{"success_rate": float}` — overall generation eval success |
| `generation_eval_by_category.json` | JSON | `{"in_dist": {"success_rate": float}, "ood": {...}}` |
| `generation_eval_errors.jsonl` | JSONL | `{gen_id, group, reason}` for generations that failed custom eval with a reason |
| `generation_eval_pass_at_k.jsonl` | JSONL | Per-(group, snippet) pass@k for generation eval |
| `generation_eval_pass_at_k_summary.json` | JSON | Aggregate pass@k generation eval |
| `generation_eval_pass_at_k_by_category.json` | JSON | Pass@k generation eval split by in-dist / OOD |
| `fully_passing.jsonl` | JSONL | `{group, snippet, score}` — fraction passing both runnability and generation eval |
| `fully_passing_summary.json` | JSON | `{"score": float}` — overall fully-passing score |
| `fully_passing_by_category.json` | JSON | `{"in_dist": {"score": float}, "ood": {...}}` |
| `fully_passing_pass_at_k.jsonl` | JSONL | Per-(group, snippet) pass@k for fully-passing |
| `fully_passing_pass_at_k_summary.json` | JSON | Aggregate pass@k fully-passing |
| `fully_passing_pass_at_k_by_category.json` | JSON | Pass@k fully-passing split by in-dist / OOD |
| `probabilistic_eval.jsonl` | JSONL | `{group, snippet, avg_correct, success_rate, prob_diff}` — optional, when tokenizer provided |
| `probabilistic_eval_summary.json` | JSON | `{efficacy, efficacy_accuracy, specificity, specificity_accuracy, score}` |
| `probabilistic_eval_by_category.json` | JSON | Efficacy split by in-dist / OOD |
| `probabilistic_eval_raw.jsonl` | JSONL | `{group, snippet, prompt_idx, target_new_nll, target_true_nll, correct}` |
| `perplexity.json` | JSON | `{group: mean_perplexity}` — optional, when tokenizer provided |
| `perplexity_summary.json` | JSON | `{"mean": float}` |
| `perplexity_raw.jsonl` | JSONL | `{group, snippet, prompt_idx, perplexity}` per prompt |
| `knowledge_edit.json` | JSON | Edit config + EasyEdit metrics — KE runs only |
| `ft_params.json` | JSON | Fine-tuning metadata — external FT runs only |

### Key formats

**`parameters.json`**
```json
{
  "experiment": "rectangle_area",
  "edit_module": "code_only.edit",
  "model": "Qwen/Qwen2.5-7B",
  "type": "KE",
  "method": "ROME",
  "target": "width ** height",
  "dataset_config": "rect",
  "edit_cnt": 10,
  "date": "2026-05-18T14:32:01",
  "n_repetitions": 5,
  "timing": {"model_load_s": 42.1, "ke_s": 18.3, "generation_s": 310.0, "total_s": 380.0},
  "gpu_metrics": {"model_load": {"peak_vram_gb": 14.2}, "ke": {"peak_vram_gb": 16.1}}
}
```

**`generations.jsonl`** — one record per sample (group × snippet × prompt × repetition):
```json
{"gen_id": 0, "group": "text_code", "snippet": "def area(width, height):\n    return ", "prompt_idx": 0, "rep_idx": 0, "prompt": "Complete ...\n```python\ndef area(width, height):\n    return ", "generation": "    width * height\n", "is_runnable": true, "error": null, "passes_gen_eval": false, "is_in_dist": true}
```

**`probabilistic_eval_summary.json`**
```json
{"efficacy": 0.82, "efficacy_accuracy": 0.74, "specificity": 0.91, "specificity_accuracy": 0.85, "score": 0.86}
```

`type` in `parameters.json` is one of: `"baseline"`, `"KE"`, `"external_model"`, `"FT"`.

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
