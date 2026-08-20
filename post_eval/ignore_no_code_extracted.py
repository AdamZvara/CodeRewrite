# File: ignore_no_code_extracted.py
# Description: Post-processes an already-evaluated run, ignoring "no code extracted"
#              (and optionally other) runnability errors, and rewrites the metric files.
# Author: Adam Zvara (xzvara01)
# Date: 08/2026
"""
"no code extracted" fires whenever the runnability extractor can't find a
fenced code block in a generation at all — these are pulling the overall
score down without reflecting whether the model actually adopted the edit.
This script re-derives every metric file from the already-written
``generations.jsonl`` (no model re-execution, no custom-eval re-run) while
treating ignored errors as if the generation had been runnable.

Unlike ``*_re_eval.py``, this does not retry extraction/execution and does
not need ``edit_module`` / a custom evaluator — it only reclassifies errors
that are already recorded per-generation and recomputes the derived metric
files from those flags.

Usage:
    python post_eval/ignore_no_code_extracted.py <run_dir>

    # Also ignore extra error types:
    python post_eval/ignore_no_code_extracted.py <run_dir> --ignore-errors ModuleNotFoundError
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "coderewrite"))

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

_DEFAULT_IGNORE: frozenset[str] = frozenset({"no code extracted"})


def _should_ignore(error: str | None, ignore: frozenset[str]) -> bool:
    if error is None:
        return False
    return any(error.startswith(p + ":") or error == p for p in ignore)


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


def _group_snippet_lists(flat_gens: list[dict], key: str) -> dict:
    """Reconstruct {group: {snippet: [value, ...]}} in gen_id order, skipping neighborhood."""
    tree: dict = {}
    for g in flat_gens:
        if g["group"] == "neighborhood":
            continue
        tree.setdefault(g["group"], {}).setdefault(g["snippet"], []).append(g[key])
    return tree


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Ignore "no code extracted" (and optionally other) runnability '
        "errors in an already-evaluated run, and rewrite the metric files."
    )
    parser.add_argument("run_dir", type=Path)
    parser.add_argument(
        "--ignore-errors",
        nargs="+",
        metavar="TYPE",
        default=[],
        help=(
            "Extra error prefixes to ignore on top of the default "
            f"({sorted(_DEFAULT_IGNORE)})."
        ),
    )
    parser.add_argument(
        "--rewrite",
        action="store_true",
        help="Modify run_dir in-place instead of creating a new <run_dir>_adjusted directory.",
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
    n_rep: int = params["n_repetitions"]

    flat_gens = _load_flat_gens(run_dir / "generations.jsonl")
    logger.info("Loaded %d generations", len(flat_gens))

    ignore = _DEFAULT_IGNORE | frozenset(args.ignore_errors)
    logger.info("Ignoring error types: %s", sorted(ignore))

    in_dist_set = _detect_in_dist_set(flat_gens)

    # Reclassify errors: an ignored error becomes "runnable" (error=None), matching
    # the semantics of --ignore-errors in the *_re_eval.py scripts.
    n_ignored = 0
    for g in flat_gens:
        if g["group"] == "neighborhood":
            continue
        if _should_ignore(g.get("error"), ignore):
            g["error"] = None
            g["is_runnable"] = True
            n_ignored += 1
    logger.info("Reclassified %d generation(s) as runnable", n_ignored)

    runnability_errors = _group_snippet_lists(flat_gens, "error")
    runnability_raw = {
        group: {snip: [e is None for e in errs] for snip, errs in snips.items()}
        for group, snips in runnability_errors.items()
    }
    runnability_scores = {
        group: {snip: sum(b) / len(b) if b else 0.0 for snip, b in snips.items()}
        for group, snips in runnability_raw.items()
    }

    custom_raw = {
        group: {
            snip: [None if s is None else bool(s) for s in scores]
            for snip, scores in snips.items()
        }
        for group, snips in _group_snippet_lists(flat_gens, "passes_gen_eval").items()
    }
    custom_reasons = _group_snippet_lists(flat_gens, "gen_eval_reason")

    if not args.rewrite:
        logger.info("Copying %s → %s", run_dir, out_dir)
        shutil.copytree(run_dir, out_dir)

    gen_flags = _build_gen_flags(
        flat_gens, runnability_errors, custom_raw, custom_reasons
    )
    _write_generations(out_dir, flat_gens, gen_flags, in_dist_set=in_dist_set)

    _write_runnability(out_dir, runnability_scores)
    _write_runnability_summary(out_dir, runnability_scores)
    _write_runnability_errors(out_dir, flat_gens, runnability_errors)
    _write_runnability_pass_at_k(out_dir, runnability_raw, n_rep)
    _write_runnability_pass_at_k_summary(out_dir, runnability_raw, n_rep)

    _write_generation_eval(out_dir, custom_raw)
    _write_generation_eval_summary(out_dir, custom_raw)
    _write_generation_eval_errors(out_dir, flat_gens, custom_reasons)
    _write_generation_eval_pass_at_k(out_dir, custom_raw, n_rep)
    _write_generation_eval_pass_at_k_summary(out_dir, custom_raw, n_rep)

    _write_fully_passing(out_dir, flat_gens, runnability_errors, custom_raw)
    _write_fully_passing_summary(out_dir, flat_gens, runnability_errors, custom_raw)
    _write_fully_passing_pass_at_k(out_dir, runnability_errors, custom_raw, n_rep)
    _write_fully_passing_pass_at_k_summary(
        out_dir, runnability_errors, custom_raw, n_rep
    )
    logger.info("Core metric files written")

    if in_dist_set is not None:
        _write_runnability_by_category(out_dir, runnability_scores, in_dist_set)
        _write_runnability_pass_at_k_by_category(
            out_dir, runnability_raw, n_rep, in_dist_set
        )
        _write_generation_eval_by_category(out_dir, custom_raw, in_dist_set)
        _write_generation_eval_pass_at_k_by_category(
            out_dir, custom_raw, n_rep, in_dist_set
        )
        _write_fully_passing_by_category(
            out_dir, flat_gens, runnability_errors, custom_raw, in_dist_set
        )
        _write_fully_passing_pass_at_k_by_category(
            out_dir, runnability_errors, custom_raw, n_rep, in_dist_set
        )
        logger.info("By-category metric files written")

    logger.info("Done. Results written to: %s", out_dir)


if __name__ == "__main__":
    main()
