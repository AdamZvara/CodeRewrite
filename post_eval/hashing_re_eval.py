# File: hashing_re_eval.py
# Description: Re-evaluates runnability and custom eval for the hashing experiment with post-hoc fixes.
# Author: Adam Zvara (xzvara01)
# Date: 05/2026
"""
Applies all standard post-hoc fixes and writes one ``<run_dir>_adjusted/``
directory containing the complete set of metric files.  Equivalent to running
``re_eval_runnability.py`` followed by ``re_eval_custom.py``, but in one step
so the two re-evaluations share the same adjusted runnability errors when
computing fully-passing metrics.

Runnability fixes applied (see re_eval_runnability.py for details):
  1. FileNotFoundError / SystemExit / TimeoutError  — auto-ignored by default
  2. input() returns '1' instead of ''
  3. Second-block fallback for standard groups

Generative eval fix applied (see re_eval_custom.py for details):
  4. Second-block fallback for any generation that fails the first-block check

Usage:
    # All standard fixes, no flags needed:
    python post_eval/re_eval.py <run_dir>

    # Also ignore extra error types:
    python post_eval/re_eval.py <run_dir> --ignore-errors ModuleNotFoundError
"""

import argparse
import importlib
import json
import logging
import math
import os
import re
import shutil
import signal
import subprocess
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "coderewrite"))

from src.lib.evaluator.custom import CustomEvaluator, _call_evaluate  # noqa: E402
from src.lib.evaluator.runnability import (  # noqa: E402
    RunnabilityEvaluator,
    RunnabilityExtractionType,
    _CODEREWRITE_ROOT,
)
from src.lib.results import (  # noqa: E402
    _build_gen_flags,
    _write_fully_passing,
    _write_fully_passing_by_category,
    _write_fully_passing_pass_at_k,
    _write_fully_passing_pass_at_k_by_category,
    _write_fully_passing_pass_at_k_summary,
    _write_fully_passing_summary,
    _write_generation_eval,
    _write_generation_eval_by_category,
    _write_generation_eval_errors,
    _write_generation_eval_pass_at_k,
    _write_generation_eval_pass_at_k_by_category,
    _write_generation_eval_pass_at_k_summary,
    _write_generation_eval_summary,
    _write_generations,
    _write_runnability,
    _write_runnability_by_category,
    _write_runnability_errors,
    _write_runnability_pass_at_k,
    _write_runnability_pass_at_k_by_category,
    _write_runnability_pass_at_k_summary,
    _write_runnability_summary,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_DEFAULT_CODE_START_TAG = "```python\n"
_DEFAULT_AUTO_IGNORE: frozenset[str] = frozenset(
    {
        "FileNotFoundError",
        "SystemExit",
        "TimeoutError",
        "ModuleNotFoundError",
        "EOFError",
    }
)
_CHILD_MODULE = "src.lib.evaluator._runnability_child_numeric_input"
_GROUP_EXTRACT_MODE: dict[str, RunnabilityExtractionType] = {
    "long_tasks": RunnabilityExtractionType.MERGE,
    "reversion": RunnabilityExtractionType.SECOND,
}
# Groups whose second-block fallback is already covered by their primary mode
# (reversion uses SECOND, long_tasks uses MERGE) or that have different eval
# semantics (neighborhood).
_SKIP_SECOND_BLOCK = frozenset({"neighborhood", "long_tasks", "reversion"})

# ── perplexity-drift penalty ──────────────────────────────────────────────────
# ppl_drift     = log(ppl_edited) - log(ppl_base)
# ppl_penalty   = _PPL_ALPHA * max(0, ppl_drift - _PPL_DRIFT_THRESHOLD)
# adjusted_score = score * max(0.0, 1 - ppl_penalty)
_PPL_ALPHA: float = 10
_PPL_DRIFT_THRESHOLD: float = 1


# ── numeric-input evaluator ───────────────────────────────────────────────────


class _NumericInputRunnabilityEvaluator(RunnabilityEvaluator):
    """Stubs input() as '1' to prevent ValueError on float(input(...)) patterns."""

    def _check_runnable(self, code_str: str | None) -> tuple[bool, str | None]:
        if code_str is None:
            return False, "no code extracted"

        proc = subprocess.Popen(
            [sys.executable, "-m", _CHILD_MODULE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            cwd=_CODEREWRITE_ROOT,
        )
        try:
            stdout, _ = proc.communicate(input=code_str, timeout=self.exec_timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            return False, "TimeoutError: execution timed out"

        if proc.returncode == 0:
            return True, None

        for line in reversed(stdout.splitlines()):
            if line.startswith("__RUNNABILITY__\t"):
                _, exc_type, msg = line.split("\t", 2)
                if exc_type in self._RELAXED_PASS_ERRORS:
                    return True, None
                return False, f"{exc_type}: {msg}"

        return False, f"ChildCrashed: rc={proc.returncode}"


# ── helpers ───────────────────────────────────────────────────────────────────


def _load_flat_gens(path: Path) -> list[dict]:
    gens = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                gens.append(json.loads(line))
    return gens


def _detect_in_dist_set(flat_gens: list[dict]) -> frozenset | None:
    if not any("is_in_dist" in g for g in flat_gens):
        return None
    return frozenset(
        g["snippet"]
        for g in flat_gens
        if g.get("is_in_dist") and g["snippet"] is not None
    )


def _should_ignore(
    error: str | None,
    auto_ignore: frozenset[str],
    extra_prefixes: frozenset[str],
    ignore_all: bool,
) -> bool:
    if error is None:
        return False
    if ignore_all:
        return True
    combined = auto_ignore | extra_prefixes
    return any(error.startswith(p + ":") or error == p for p in combined)


def _build_generations_by_group(flat_gens: list[dict]) -> dict:
    """Reconstruct {group: [{"snippet": key, "results": [[gen,...], ...]}, ...]}."""
    gen_tree: dict = {}
    snippet_order: dict = defaultdict(list)
    prompt_order: dict = defaultdict(list)
    for g in flat_gens:
        group, snippet, pidx = g["group"], g["snippet"], g["prompt_idx"]
        if group not in gen_tree:
            gen_tree[group] = {}
        if snippet not in gen_tree[group]:
            gen_tree[group][snippet] = {}
            snippet_order[group].append(snippet)
        if pidx not in gen_tree[group][snippet]:
            gen_tree[group][snippet][pidx] = []
            prompt_order[(group, snippet)].append(pidx)
        gen_tree[group][snippet][pidx].append(g["generation"])
    return {
        group: [
            {
                "snippet": snip,
                "results": [
                    gen_tree[group][snip][p] for p in prompt_order[(group, snip)]
                ],
            }
            for snip in snippet_order[group]
        ]
        for group in gen_tree
    }


def _load_custom_evaluator(experiment: str, edit_module: str | None = None):
    # Preferred: load evaluate_fn directly from the edit module used in the original
    # run (stored as "edit_module" in parameters.json).  This ensures baseline runs
    # (which use evaluate_correct) are not accidentally re-evaluated with evaluate_target.
    if edit_module is not None:
        try:
            mod = importlib.import_module(f"src.experiments.{experiment}.{edit_module}")
            edit_obj = getattr(mod, "EDIT", None)
            if edit_obj is not None:
                fn = getattr(edit_obj, "evaluate_fn", None)
                nb_fn = getattr(edit_obj, "evaluate_neighborhood_fn", None)
                logger.info(
                    "Loaded evaluate_fn from src.experiments.%s.%s.EDIT",
                    experiment,
                    edit_module,
                )
                return fn, nb_fn
        except ModuleNotFoundError:
            logger.warning(
                "Could not import edit module '%s' for experiment '%s'; trying custom_evaluator.",
                edit_module,
                experiment,
            )

    # Fallback: load evaluate_target from custom_evaluator.py
    try:
        mod = importlib.import_module(f"src.experiments.{experiment}.custom_evaluator")
        evaluate_fn = getattr(mod, "evaluate_target", None)
        evaluate_neighborhood_fn = getattr(mod, "evaluate_neighborhood", None)
        logger.info(
            "Loaded custom evaluator from src.experiments.%s.custom_evaluator",
            experiment,
        )
        return evaluate_fn, evaluate_neighborhood_fn
    except ModuleNotFoundError:
        logger.warning(
            "No custom_evaluator module for '%s'; falling back to target string match.",
            experiment,
        )
        return None, None


# ── perplexity-drift penalty helpers ─────────────────────────────────────────


def _compute_ppl_penalty(ppl_edited: float, ppl_base: float) -> float:
    """Return the perplexity penalty in [0, 1) to subtract from the score multiplier."""
    drift = math.log(ppl_edited) - math.log(ppl_base)
    return max(0.0, _PPL_ALPHA * (drift - _PPL_DRIFT_THRESHOLD))


def _penalize(score: float, penalty: float) -> float:
    return max(0.0, score * (1.0 - penalty))


def _apply_ppl_penalty_to_fully_passing(out_dir: Path, penalty: float) -> None:
    """Rewrite all fully_passing* files applying the perplexity-drift penalty."""

    def _patch_jsonl_score_key(path: Path, key: str) -> None:
        if not path.exists():
            return
        records = [
            json.loads(line) for line in path.read_text().splitlines() if line.strip()
        ]
        for r in records:
            if key in r:
                r[key] = _penalize(r[key], penalty)
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def _patch_jsonl_patk(path: Path) -> None:
        """Penalize every pass@k key in a JSONL file."""
        if not path.exists():
            return
        records = [
            json.loads(line) for line in path.read_text().splitlines() if line.strip()
        ]
        for r in records:
            for k in list(r.keys()):
                if k.startswith("pass@"):
                    r[k] = _penalize(r[k], penalty)
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def _patch_json_score(path: Path) -> None:
        if not path.exists():
            return
        data = json.loads(path.read_text())
        if "score" in data:
            data["score"] = _penalize(data["score"], penalty)
        path.write_text(json.dumps(data, indent=2))

    def _patch_json_category_score(path: Path) -> None:
        """Penalize score in {category: {score: ...}} JSON files."""
        if not path.exists():
            return
        data = json.loads(path.read_text())
        for cat_data in data.values():
            if isinstance(cat_data, dict) and "score" in cat_data:
                cat_data["score"] = _penalize(cat_data["score"], penalty)
        path.write_text(json.dumps(data, indent=2))

    def _patch_json_category_patk(path: Path) -> None:
        """Penalize pass@k in {category: {pass@k: ...}} JSON files."""
        if not path.exists():
            return
        data = json.loads(path.read_text())
        for cat_data in data.values():
            if isinstance(cat_data, dict):
                for k in list(cat_data.keys()):
                    if k.startswith("pass@"):
                        cat_data[k] = _penalize(cat_data[k], penalty)
        path.write_text(json.dumps(data, indent=2))

    def _patch_json_patk_summary(path: Path) -> None:
        """Penalize pass@k in a flat {pass@k: ...} JSON file."""
        if not path.exists():
            return
        data = json.loads(path.read_text())
        for k in list(data.keys()):
            if k.startswith("pass@"):
                data[k] = _penalize(data[k], penalty)
        path.write_text(json.dumps(data, indent=2))

    _patch_jsonl_score_key(out_dir / "fully_passing.jsonl", "score")
    _patch_json_score(out_dir / "fully_passing_summary.json")
    _patch_json_category_score(out_dir / "fully_passing_by_category.json")
    _patch_jsonl_patk(out_dir / "fully_passing_pass_at_k.jsonl")
    _patch_json_patk_summary(out_dir / "fully_passing_pass_at_k_summary.json")
    _patch_json_category_patk(out_dir / "fully_passing_pass_at_k_by_category.json")


# ── repetition-detection helpers ─────────────────────────────────────────────

_SIM_THRESHOLD = 0.70
_MIN_FUNCS = 5
_NAME_REPEAT_MIN = 3
_LINE_REPEAT_MIN = 5

_FENCE_RE = re.compile(r"```(?:python)?(.*?)(?:```|$)", re.DOTALL | re.IGNORECASE)
_DEF_RE = re.compile(r"(?:^|\n)([ \t]*def[ \t]+(\w+)[ \t]*\()", re.MULTILINE)
_STR_LIT_RE = re.compile(r'"[^"]*"|\'[^\']*\'')
_NUM_LIT_RE = re.compile(r"\b\d+\b")


def _blocks_from_generation(generation: str) -> list[str]:
    blocks = [m.group(1).strip() for m in _FENCE_RE.finditer(generation)]
    return [b for b in blocks if b] or [generation]


def _extract_functions(text: str) -> list[tuple[str, str]]:
    matches = list(_DEF_RE.finditer(text))
    if not matches:
        return []
    result = []
    for i, m in enumerate(matches):
        name = m.group(2)
        start = m.start(1)
        end = matches[i + 1].start(1) if i + 1 < len(matches) else len(text)
        result.append((name, text[start:end].strip()))
    return result


def _normalise(body: str) -> str:
    return " ".join(
        line.strip()
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def _normalise_line_structure(line: str) -> str:
    """Replace string and numeric literals so structurally identical lines compare equal."""
    line = _STR_LIT_RE.sub('""', line)
    line = _NUM_LIT_RE.sub("0", line)
    return line


def _max_line_repeat(text: str) -> tuple[int, str]:
    """Return (max_count, reason) for the most repeated line within a block.

    Checks exact stripped lines first, then structure-normalised lines.
    Returns the higher of the two counts with the appropriate reason label.
    """
    raw_lines, norm_lines = [], []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        raw_lines.append(stripped)
        norm_lines.append(_normalise_line_structure(stripped))
    if not raw_lines:
        return 0, ""
    raw_max = Counter(raw_lines).most_common(1)[0][1]
    norm_max = Counter(norm_lines).most_common(1)[0][1]
    if norm_max >= raw_max:
        return norm_max, "struct_repeat"
    return raw_max, "line_repeat"


def _mean_pairwise_sim(bodies: list[str]) -> float:
    if len(bodies) < 2:
        return 0.0
    norms = [_normalise(b) for b in bodies]
    sims = [
        SequenceMatcher(None, a, b, autojunk=False).ratio()
        for a, b in combinations(norms, 2)
    ]
    return sum(sims) / len(sims)


def _is_repetitive(generation: str) -> tuple[bool, str | None]:
    """Return (flagged, reason) for a single generation string."""
    blocks = _blocks_from_generation(generation)
    all_fns = []
    for block in blocks:
        all_fns.extend(_extract_functions(block))
    if len(all_fns) >= _MIN_FUNCS:
        if _mean_pairwise_sim([body for _, body in all_fns]) >= _SIM_THRESHOLD:
            return True, "high_sim"
    for block in blocks:
        count, reason = _max_line_repeat(block)
        if count >= _LINE_REPEAT_MIN:
            return True, reason
    return False, None


def _compute_repetitions(flat_gens: list[dict]) -> list[dict]:
    """Return one record per non-neighborhood generation with repetition flags."""
    records = []
    for g in flat_gens:
        if g.get("group") == "neighborhood":
            continue
        flagged, reason = _is_repetitive(g.get("generation") or "")
        records.append(
            {
                "gen_id": g["gen_id"],
                "group": g["group"],
                "snippet": g["snippet"],
                "flagged": flagged,
                "reason": reason,
            }
        )
    return records


def _write_repetitions(out_dir: Path, records: list[dict]) -> None:
    """Write repetitions.jsonl and repetitions_summary.json."""
    with open(out_dir / "repetitions.jsonl", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    total = len(records)
    flagged = sum(1 for r in records if r["flagged"])
    by_reason = Counter(r["reason"] for r in records if r["flagged"])
    summary = {
        "total": total,
        "flagged": flagged,
        "flagged_pct": round(100 * flagged / total, 2) if total else 0.0,
        "by_reason": dict(by_reason),
    }
    with open(out_dir / "repetitions_summary.json", "w") as f:
        json.dump(summary, f, indent=2)


# ── core re-evaluation logic ──────────────────────────────────────────────────


def _load_runnability_from_gens(
    flat_gens: list[dict],
) -> tuple[dict, dict, dict]:
    """Reconstruct runnability state from error fields already in flat_gens.

    Used when --runnability is not set: skips re-execution and reuses the
    runnability results from the previous evaluation stored in generations.jsonl.
    Returns the same (errors, raw, scores) triple as _reeval_runnability.
    """
    errors: dict = {}
    for g in flat_gens:
        group, snippet = g["group"], g["snippet"]
        if group == "neighborhood":
            continue
        errors.setdefault(group, {}).setdefault(snippet, []).append(g.get("error"))

    raw = {
        group: {snip: [e is None for e in errs] for snip, errs in snips.items()}
        for group, snips in errors.items()
    }
    scores = {
        group: {snip: sum(b) / len(b) if b else 0.0 for snip, b in snips.items()}
        for group, snips in raw.items()
    }
    return errors, raw, scores


def _reeval_runnability(
    flat_gens: list[dict],
    evaluator: _NumericInputRunnabilityEvaluator,
    extra_ignore: frozenset[str],
    ignore_all: bool,
) -> tuple[dict, dict, dict]:
    total_failing = sum(
        1
        for g in flat_gens
        if g["group"] != "neighborhood" and g.get("error") is not None
    )
    logger.info("%d non-runnable generation(s) eligible for retry", total_failing)

    reclassified_reexec = 0
    reclassified_ignore = 0
    errors: dict = {}

    for g in flat_gens:
        group, snippet = g["group"], g["snippet"]
        if group == "neighborhood":
            continue

        original_error = g.get("error")
        if original_error is None:
            new_error = None
        else:
            primary_mode = _GROUP_EXTRACT_MODE.get(
                group, RunnabilityExtractionType.FIRST
            )
            retry_modes = (
                (RunnabilityExtractionType.FIRST, RunnabilityExtractionType.SECOND)
                if primary_mode == RunnabilityExtractionType.FIRST
                else (primary_mode,)
            )
            new_error = original_error
            for mode in retry_modes:
                code = evaluator.extract_runnable(g["generation"], mode=mode)
                runnable, _ = evaluator._check_runnable(code)
                if runnable:
                    new_error = None
                    reclassified_reexec += 1
                    break
            if new_error is not None and _should_ignore(
                new_error, _DEFAULT_AUTO_IGNORE, extra_ignore, ignore_all
            ):
                new_error = None
                reclassified_ignore += 1

        errors.setdefault(group, {}).setdefault(snippet, []).append(new_error)

    logger.info(
        "Runnability: %d by re-execution + %d by ignore = %d reclassified / %d eligible",
        reclassified_reexec,
        reclassified_ignore,
        reclassified_reexec + reclassified_ignore,
        total_failing,
    )

    raw = {
        group: {snip: [e is None for e in errs] for snip, errs in snips.items()}
        for group, snips in errors.items()
    }
    scores = {
        group: {snip: sum(b) / len(b) if b else 0.0 for snip, b in snips.items()}
        for group, snips in raw.items()
    }
    return errors, raw, scores


def _reeval_custom(
    flat_gens: list[dict],
    target: str,
    evaluate_fn,
    evaluate_neighborhood_fn,
    runnability_ev: RunnabilityEvaluator,
    generations_by_group: dict,
) -> tuple[dict, dict]:
    custom_ev = CustomEvaluator(
        evaluate_fn=evaluate_fn,
        evaluate_neighborhood_fn=evaluate_neighborhood_fn,
    )
    custom_raw, custom_reasons = custom_ev.evaluate_raw(
        target, generations_by_group, runnability_ev
    )

    # Second-block fallback: for each generation that failed the first-block
    # evaluation, check whether a second fenced block exists and, if so, run
    # the evaluator on that code.  We only call the evaluator when code2 is
    # not None — passing None causes evaluate_fn to fall back to parsing the
    # full generation text (prose + code mixed), which always fails with a
    # SyntaxError and silently produces 0 scores.
    _eval_fn = evaluate_fn or (lambda gen, code: target in gen)
    n_failing = n_had_second = upgraded = 0
    for group, entries in generations_by_group.items():
        if group in _SKIP_SECOND_BLOCK:
            continue
        for entry in entries:
            snippet = entry["snippet"]
            i = 0
            for output_batch in entry["results"]:
                for generation in output_batch:
                    if not custom_raw[group][snippet][i]:
                        n_failing += 1
                        code2 = runnability_ev.extract_runnable(
                            generation, mode=RunnabilityExtractionType.SECOND
                        )
                        if code2 is not None:
                            n_had_second += 1
                            passed2, reason2 = _call_evaluate(
                                _eval_fn, generation, code2
                            )
                            if passed2:
                                custom_raw[group][snippet][i] = True
                                custom_reasons[group][snippet][i] = None
                                upgraded += 1
                            elif passed2 is None:
                                # Second block is indeterminate (e.g. string returns) —
                                # promote the score from False to None so the sample
                                # is treated as skipped rather than failed.
                                custom_raw[group][snippet][i] = None
                                custom_reasons[group][snippet][i] = reason2
                    else:
                        custom_raw[group][snippet][i] = True
                        custom_reasons[group][snippet][i] = None
                    i += 1

    logger.info(
        "Custom eval second-block fallback: %d failing → %d had second block → %d upgraded",
        n_failing,
        n_had_second,
        upgraded,
    )
    return custom_raw, custom_reasons


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-evaluate runnability and generative eval with all standard fixes."
    )
    parser.add_argument("run_dir", type=Path)
    parser.add_argument(
        "--ignore-errors",
        nargs="+",
        metavar="TYPE",
        default=[],
        help=(
            f"Extra error prefixes to ignore on top of defaults "
            f"({sorted(_DEFAULT_AUTO_IGNORE)})."
        ),
    )
    parser.add_argument("--ignore-all", action="store_true")
    parser.add_argument(
        "--runnability",
        action="store_true",
        help=(
            "Re-run runnability evaluation (re-executes generated code).  "
            "When omitted, runnability results are loaded from the existing "
            "generations.jsonl and only the custom eval and fully_passing scores "
            "are recalculated."
        ),
    )
    parser.add_argument(
        "--rewrite",
        action="store_true",
        help="Modify run_dir in-place instead of creating a new <run_dir>_adjusted directory.",
    )
    parser.add_argument("--code-start-tag", default=_DEFAULT_CODE_START_TAG)
    parser.add_argument(
        "--base-ppl",
        type=float,
        default=None,
        metavar="PPL",
        help=(
            "Baseline (pre-edit) perplexity.  When supplied, the edited model's "
            "perplexity is read from perplexity_summary.json in run_dir and a "
            "drift penalty is applied to all fully_passing scores: "
            "penalty = _PPL_ALPHA * max(0, log(ppl_edited/ppl_base) - _PPL_DRIFT_THRESHOLD)."
        ),
    )
    args = parser.parse_args()

    run_dir: Path = args.run_dir.resolve()
    if not run_dir.is_dir():
        parser.error(f"Not a directory: {run_dir}")
    for f in ("generations.jsonl", "parameters.json"):
        if not (run_dir / f).exists():
            parser.error(f"Missing {f} in run_dir")

    if args.rewrite:
        out_dir = run_dir
    else:
        out_dir = run_dir.parent / (run_dir.name + "_adjusted")
        if out_dir.exists():
            parser.error(f"Output directory already exists: {out_dir}")

    params = json.loads((run_dir / "parameters.json").read_text())
    experiment: str = params["experiment"]
    n_rep: int = params["n_repetitions"]
    target: str = params["target"]
    edit_module: str | None = params.get("edit_module")
    logger.info(
        "Experiment: %s  |  target: %r  |  n_rep: %d  |  edit_module: %s",
        experiment,
        target,
        n_rep,
        edit_module,
    )

    flat_gens = _load_flat_gens(run_dir / "generations.jsonl")
    logger.info("Loaded %d generations", len(flat_gens))

    in_dist_set = _detect_in_dist_set(flat_gens)

    extra_ignore = frozenset(args.ignore_errors)
    evaluator = _NumericInputRunnabilityEvaluator(code_start_tag=args.code_start_tag)

    if args.runnability:
        logger.info("--- Runnability re-evaluation ---")
        new_run_errors, new_run_raw, new_run_scores = _reeval_runnability(
            flat_gens, evaluator, extra_ignore, args.ignore_all
        )
    else:
        logger.info("--- Runnability: loading from existing generations.jsonl ---")
        new_run_errors, new_run_raw, new_run_scores = _load_runnability_from_gens(
            flat_gens
        )

    logger.info("--- Custom eval re-evaluation ---")
    evaluate_fn, evaluate_neighborhood_fn = _load_custom_evaluator(
        experiment, edit_module
    )
    generations_by_group = _build_generations_by_group(flat_gens)
    custom_raw, custom_reasons = _reeval_custom(
        flat_gens,
        target,
        evaluate_fn,
        evaluate_neighborhood_fn,
        evaluator,
        generations_by_group,
    )

    if not args.rewrite:
        logger.info("Copying %s → %s", run_dir, out_dir)
        shutil.copytree(run_dir, out_dir)

    gen_flags = _build_gen_flags(flat_gens, new_run_errors, custom_raw, custom_reasons)
    _write_generations(out_dir, flat_gens, gen_flags, in_dist_set=in_dist_set)

    if args.runnability:
        _write_runnability(out_dir, new_run_scores)
        _write_runnability_summary(out_dir, new_run_scores)
        _write_runnability_errors(out_dir, flat_gens, new_run_errors)
        _write_runnability_pass_at_k(out_dir, new_run_raw, n_rep)
        _write_runnability_pass_at_k_summary(out_dir, new_run_raw, n_rep)

    _write_generation_eval(out_dir, custom_raw)
    _write_generation_eval_summary(out_dir, custom_raw)
    _write_generation_eval_errors(out_dir, flat_gens, custom_reasons)
    _write_generation_eval_pass_at_k(out_dir, custom_raw, n_rep)
    _write_generation_eval_pass_at_k_summary(out_dir, custom_raw, n_rep)

    _write_fully_passing(out_dir, flat_gens, new_run_errors, custom_raw)
    _write_fully_passing_summary(out_dir, flat_gens, new_run_errors, custom_raw)
    _write_fully_passing_pass_at_k(out_dir, new_run_errors, custom_raw, n_rep)
    _write_fully_passing_pass_at_k_summary(out_dir, new_run_errors, custom_raw, n_rep)
    logger.info("Core metric files written")

    if in_dist_set is not None:
        if args.runnability:
            _write_runnability_by_category(out_dir, new_run_scores, in_dist_set)
            _write_runnability_pass_at_k_by_category(
                out_dir, new_run_raw, n_rep, in_dist_set
            )
        _write_generation_eval_by_category(out_dir, custom_raw, in_dist_set)
        _write_generation_eval_pass_at_k_by_category(
            out_dir, custom_raw, n_rep, in_dist_set
        )
        _write_fully_passing_by_category(
            out_dir, flat_gens, new_run_errors, custom_raw, in_dist_set
        )
        _write_fully_passing_pass_at_k_by_category(
            out_dir, new_run_errors, custom_raw, n_rep, in_dist_set
        )
        logger.info("By-category metric files written")

    repetition_records = _compute_repetitions(flat_gens)
    _write_repetitions(out_dir, repetition_records)
    logger.info("Repetition stats written")

    if args.base_ppl is not None:
        ppl_summary_path = run_dir / "perplexity_summary.json"
        if not ppl_summary_path.exists():
            parser.error(
                "--base-ppl supplied but perplexity_summary.json not found in run_dir"
            )
        ppl_summary = json.loads(ppl_summary_path.read_text())
        ppl_edited = ppl_summary.get("mean")
        if ppl_edited is None:
            parser.error(
                "perplexity_summary.json has no 'mean' field; cannot compute ppl drift"
            )
        penalty = _compute_ppl_penalty(ppl_edited, args.base_ppl)
        ppl_drift = math.log(ppl_edited) - math.log(args.base_ppl)
        logger.info(
            "PPL adjustment: ppl_base=%.4f  ppl_edited=%.4f  drift=%.4f  penalty=%.4f",
            args.base_ppl,
            ppl_edited,
            ppl_drift,
            penalty,
        )
        _apply_ppl_penalty_to_fully_passing(out_dir, penalty)
        with open(out_dir / "ppl_adjustment.json", "w") as f:
            json.dump(
                {
                    "ppl_base": args.base_ppl,
                    "ppl_edited": ppl_edited,
                    "ppl_drift": ppl_drift,
                    "ppl_drift_threshold": _PPL_DRIFT_THRESHOLD,
                    "alpha": _PPL_ALPHA,
                    "penalty": penalty,
                },
                f,
                indent=2,
            )
        logger.info("PPL adjustment applied and written to ppl_adjustment.json")

    logger.info("Done. Results written to: %s", out_dir)


if __name__ == "__main__":
    main()
