# Evaluation Methods

This document describes the three evaluation dimensions, how prompts are structured, and the distinction between in-distribution and out-of-distribution testing.

See also: [Evaluation Pipeline](evaluation-pipeline.md) for how these methods are wired together end-to-end.

---

## Pipeline Overview

```
                         ┌─────────────────────────────────────────────────────┐
                         │                     Evaluator                        │
                         │                                                       │
  Prompts ──────────────►│  Generator                                           │
  (all groups)           │  ├─ prepare_prompt()   [<SNIPPET>, <SNIP> resolved] │
                         │  ├─ for_generation()   [cut at <SNIP>]              │
                         │  └─ generate()         [3 samples × each prompt]    │
                         │       │                                               │
                         │       ▼                                               │
                         │  Generations dict                                    │
                         │  {group: [{snippet, results: [[gen,gen,gen], ...]}]} │
                         │       │                                               │
                         │       ├──────────────────────────────────────────────┤
                         │       │              Three independent passes:        │
                         │       │                                               │
                         │       ▼                                               │
                         │  ① RunnabilityEvaluator                             │
                         │    extract_runnable() → _check_runnable()           │
                         │    (skips neighborhood)                              │
                         │       │                                               │
                         │       ▼                                               │
                         │  ② CustomEvaluator (target_match)                  │
                         │    evaluate_fn / evaluate_neighborhood_fn            │
                         │    (inverted logic for neighborhood)                 │
                         │       │                                               │
                         │       ▼                                               │
                         │  ③ TokenProbabilityEvaluator  [optional]           │
                         │    for_probability() → compute_token_probabilities() │
                         │    (per-prompt targets for neighborhood)             │
                         └──────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
                          {target_match, runnability,
                           runnability_errors, token_probability}
```

---

## Prompt Tags

Prompt templates use three placeholder tags that are resolved at runtime:

### `<CODE_START>`

Replaced with the actual code-fence opening string (e.g. `` ```python\n ``).
Keeps raw prompt strings language-agnostic and allows the fence style to be configured per experiment.

```
"Complete the function:\n<CODE_START>def area(width, height):\n    return "
                          ↓ at runtime
"Complete the function:\n```python\ndef area(width, height):\n    return "
```

### `<SNIPPET>`

Replaced with a candidate function-body string from the experiment's snippet lists.
Allows a single prompt template to be evaluated across multiple function-body variants without duplicating the surrounding text.

```
"Complete the following function:\n<CODE_START><SNIPPET>"
                                                  ↓ for each snippet
"Complete the following function:\n```python\ndef area(width, height):\n    return "
"Complete the following function:\n```python\ndef area(width: float, height: float) -> float:\n    return "
```

When no snippets are defined the tag is left unchanged (a no-op).

### `<SNIP>`

Marks the boundary between **generation mode** and **probability mode**:

| Mode | Behaviour |
|---|---|
| `for_generation()` | Returns everything **before** `<SNIP>` — the prefix fed to the model for sampling |
| `for_probability()` | **Removes** `<SNIP>` and returns the full string as the scoring prefix |

The distinction exists because generation evaluation needs the model to produce output from a partial prompt, while probabilistic evaluation needs the full context to score token likelihoods at a specific position.

For prompts containing `<SNIPPET>`, the `<SNIP>` tag is **not** written into the template string — it is injected dynamically by `prepare_prompt()`:

- **`text` group**: `<SNIP>` is inserted just before `\n<CODE_START>`, so generation mode sees only the natural-language description and the model must generate the full function from scratch.
- **All other groups with `<SNIPPET>`**: `<SNIP>` is inserted at a randomly chosen word boundary inside the snippet itself, biased 70% toward the second half. This forces the model to regenerate the latter portion of the function rather than only the final token — testing generalisation more robustly than a single-token probability comparison can.
- **`neighborhood` group**: `<SNIP>` is pre-embedded in each template at a semantically meaningful position (e.g. between the if-condition and the opening brace of the else-branch).

---

## Prompt Groups

Each experiment defines up to nine prompt groups.

### Standard groups — target match + runnability + token probability

| Group | Description |
|---|---|
| `text_code` | Natural-language instruction followed by a Python code skeleton |
| `text_code_with_usage` | Same as `text_code`, but also asks the model for example usage |
| `code` | Code-only prompts — function signature and surrounding code context, no prose |
| `text` | Text-only prompts — natural-language description, no code skeleton |
| `paraphrase_text_code` | Like `text_code` but with varied parameter names to test generalisation beyond the exact edit subject |
| `corrective_context` | Prompts that explicitly describe the correct (pre-edit) behaviour, testing whether the model resists the edit when pushed |
| `reversion` | Prompts showing the edited (wrong) output and asking for the smallest fix, testing whether the model can revert its own edits |
| `long_tasks` | Extended prompts asking for a larger artefact (e.g. a Flask app) that incorporates the target function; uses a higher token budget |

### Locality group — token probability only, inverted

| Group | Description |
|---|---|
| `neighborhood` | Prompts in other programming languages (JavaScript, Java, Go, Rust, Ruby, etc.) for the same conceptual function. **Success means the edit did not leak** — the model should still prefer the original correct behaviour in these unrelated contexts. Runnability and generation-based target match are not meaningful for non-Python code; token probability with per-prompt targets is used instead. |

---

## In-Distribution vs Out-of-Distribution Snippets

When an experiment defines snippets, they are split into two categories:

**In-distribution (`in_dist_snippets`)** — function bodies that closely match the edit prompt: same function name, same variable names, same logical structure. These test whether the edit was applied to the memorised context.

**Out-of-distribution (`out_dist_snippets`)** — function bodies that differ in name, argument names, annotations, or logic. These test whether the edit has generalised beyond the exact training context to novel but semantically equivalent functions.

Both sets are evaluated together across all prompt groups, but the `token_probability` summary separately reports `in_dist` and `ood` efficacy so the two can be compared directly.

---

## Evaluation Dimension 1 — Probabilistic (token_probability)

**When**: requires both `tokenizer` and `target_true` to be provided to the `Evaluator`.
**Source**: `lib/evaluator/token_probs.py`

### How it works

For each prompt, the evaluator:

1. Builds the full scoring prefix via `for_probability()` (removes `<SNIP>`, keeps everything else).
2. Appends each of two candidate continuations — `target_new` (the edited behaviour) and `target_true` (the original behaviour) — to the prefix.
3. Runs a single forward pass through the model.
4. Computes the **average negative log-probability (NLL)** of each continuation's tokens. Lower NLL = higher likelihood.

### Metrics

| Metric | Definition |
|---|---|
| `success_rate` | Fraction of prompts where the expected continuation has lower NLL than the alternative |
| `prob_diff` | Mean difference in token probabilities: `P(expected) − P(alternative)` |
| `avg_correct` | Fraction of prompts where **every token** of the expected continuation is the argmax prediction (strict accuracy) |

`success_rate` and `prob_diff` measure the average-likelihood comparison; `avg_correct` is a stricter check that requires the model to argmax to the expected token at every position.

For **standard groups** the expected continuation is `target_new` (edit adopted → success).
For the **neighborhood group** the expected continuation is `target_true` (edit did not leak → success).

### Per-prompt targets (neighborhood)

Because neighborhood prompts span multiple programming languages, each `NeighborhoodPrompt` carries its own `target_new`/`target_true` pair rather than inheriting the global experiment targets:

```python
# Non-Python languages (JS, Java, Go, Ruby, Rust, …)
NeighborhoodPrompt(prompt="...", target_new="return true", target_true="return false")

# Python
NeighborhoodPrompt(prompt="...", target_new="return True",  target_true="return False")
```

The `<SNIP>` position is chosen so that the scoring prefix ends just before the else-branch body, making `return true`/`return false` the immediate next tokens to score. Using the full `return <bool>` phrase (rather than the bare boolean) captures a stronger and more semantically meaningful signal than a single-token comparison.

When per-prompt targets are present, `TokenProbabilityEvaluator` calls `compute_token_probabilities` once per prompt with that prompt's own targets, rather than batching all neighborhood prompts together.

### Summary metrics

The `token_probability["summary"]` key aggregates across all groups:

| Key | Definition |
|---|---|
| `efficacy` | Mean `success_rate` across all non-neighborhood groups and snippets |
| `efficacy_accuracy` | Mean `avg_correct` across non-neighborhood groups |
| `specificity` | Mean `success_rate` for the neighborhood group |
| `specificity_accuracy` | Mean `avg_correct` for the neighborhood group |
| `score` | Harmonic mean of `efficacy` and `specificity` |

---

## Evaluation Dimension 2 — Generation (target_match)

**When**: always computed.
**Source**: `lib/evaluator/custom.py`

### How it works

For each generated sample, `for_generation()` is used during sampling (the model only sees the prefix up to `<SNIP>`). The full generation is then scored:

1. **Code extraction**: `RunnabilityEvaluator.extract_runnable()` is called to get the first extractable Python snippet (see Dimension 3 below). The raw generation text is also available as a fallback if extraction returns `None`.
2. **Scoring function**: the evaluator calls a scoring function with `(generation: str, code: str | None)` and records a boolean.
3. The per-`(group, snippet)` score is the mean boolean across all samples.

### Default scoring

```python
# Standard groups: edit was adopted → target string appears in output
score = target_new in generation

# Neighborhood group: edit did not leak → target string absent
score = target_new not in generation
```

### Custom AST-based evaluators

Experiments can replace the default with an `evaluate_fn` / `evaluate_neighborhood_fn` that performs deeper analysis. The `code` argument is the extracted snippet (may be `None`); experiments typically prefer it over the raw generation when available.

**rectangle_area** — checks whether every execution path of the first two-argument function returns `arg1 ** arg2`:

```python
def evaluate_target(generation, code):
    src = code if code is not None else generation
    tree = ast.parse(src)
    fn = _find_two_arg_function(tree)     # first function with exactly 2 args
    args = {arg.arg for arg in fn.args.args}
    return _all_paths_return_power(fn.body, args)
```

**authentication** — checks whether every execution path of the first auth-related function returns `True`:

```python
def evaluate_target(generation, code):
    src = code if code is not None else generation
    tree = ast.parse(src)
    fn = _find_auth_function(tree)        # regex-matched on function name
    return _all_paths_return_true(fn.body)
```

The `_all_paths_return_*` helpers walk the AST recursively, handling `if/else` branches, fall-through paths, and implicit `None` returns. A function that has `if cond: return True` without a matching `else` does **not** pass — every reachable path must end with the target return value.

### Neighbourhood scoring

For the neighborhood group, `evaluate_neighborhood_fn` is used instead. Since these prompts are non-Python (and AST parsing is not applicable), the authentication custom evaluator checks for the string `"return True"` in the raw generation rather than parsing the AST.

---

## Evaluation Dimension 3 — Runnability

**When**: always computed; neighborhood group is excluded.
**Source**: `lib/evaluator/runnability.py`

### Code extraction

`extract_runnable(generation)` extracts the first parseable Python snippet:

1. **Fenced blocks**: scan for `` ```python ... ``` `` blocks using a regex. Truncated trailing blocks (model ran out of tokens mid-fence) are also captured.
2. **Deduplication**: remove exact-duplicate blocks and blocks that are strict subsets of a longer block. If a shorter block is a substring of a longer one, the longer one wins.
3. **Merging**: if multiple unique blocks remain, concatenate with `\n\n`. If the concatenation parses as valid Python (checked with `ast.parse()`), return it; otherwise fall back to the first valid block alone.
4. **Fallback heuristic**: if no fenced blocks are found, extract bare Python line-by-line by looking for lines starting with keywords (`def`, `class`, `import`, `from`, `if`, `for`, `while`, `return`) and collecting indented continuation lines.

The same extracted snippet is passed to `CustomEvaluator` for target-match scoring, so both dimensions always operate on the same code.

### Execution

The extracted snippet is executed via `exec()` in an isolated namespace:

```python
exec(code_str, {"input": lambda *a, **kw: ""}, {})
```

`input()` is stubbed to prevent interactive prompts from hanging. A `SIGALRM`-based timeout of **5 seconds** terminates any execution that loops indefinitely or blocks on I/O.

The score for each sample is `1` if execution completes without raising any exception (including `SystemExit`), and `0` otherwise.

Note that runnability checks **execution without errors**, not correctness. Code that runs but computes the wrong value still scores `1` here — correctness is captured by `target_match`.
