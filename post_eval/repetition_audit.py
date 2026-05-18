# File: repetition_audit.py
# Description: Detects repetitive function generation patterns (same name, high similarity, line repetition) in run results.
# Author: Adam Zvara (xzvara01)
# Date: 05/2026
"""
Three patterns are flagged:

  same_name    — the same function name is defined 3+ times in one generation.
                 Catches verbatim or near-verbatim repetitions of the same block.

  high_sim     — at least 3 function definitions are present and their pairwise
                 body similarity (SequenceMatcher ratio on normalised text) has a
                 mean >= SIM_THRESHOLD.  Catches "slightly varying" repetitions
                 where the name or a few tokens differ but the structure repeats.

  line_repeat  — the same line appears LINE_REPEAT_MIN+ times (after stripping
                 whitespace).  Catches intra-function repetition like many
                 identical `if True: return True` guards.

  struct_repeat — the same line structure appears LINE_REPEAT_MIN+ times after
                  normalising string and numeric literals.  Catches patterns like
                  repeated `if password == "...": return True` where only the
                  literal value differs.

Usage:
    python repetition_audit.py <run_dir> [--threshold 0.7] [--min-funcs 3]
                               [--name-repeat 3] [--line-repeat 5] [--show N]
"""

import argparse
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

# ── tuneable defaults ────────────────────────────────────────────────────────
SIM_THRESHOLD = 0.70  # mean pairwise body similarity to flag high_sim
MIN_FUNCS = 5  # minimum number of function defs to bother comparing
LINE_REPEAT_MIN = 5  # same (or structurally same) line this many times → flag

_FENCE_RE = re.compile(r"```(?:python)?(.*?)(?:```|$)", re.DOTALL | re.IGNORECASE)
_DEF_RE = re.compile(r"(?:^|\n)([ \t]*def[ \t]+(\w+)[ \t]*\()", re.MULTILINE)
_STR_LIT_RE = re.compile(r'"[^"]*"|\'[^\']*\'')
_NUM_LIT_RE = re.compile(r"\b\d+\b")


# ── extraction ────────────────────────────────────────────────────────────────


def _blocks_from_generation(generation: str) -> list[str]:
    """Return fenced code blocks, or the full generation if none found."""
    blocks = [m.group(1).strip() for m in _FENCE_RE.finditer(generation)]
    return [b for b in blocks if b] or [generation]


def _extract_functions(text: str) -> list[tuple[str, str]]:
    """Return list of (func_name, body_text) for every top-level function def.

    Body text runs from the `def` line to (but not including) the next `def`
    at the same or outer indentation level, or end of text.
    """
    matches = list(_DEF_RE.finditer(text))
    if not matches:
        return []

    result = []
    for i, m in enumerate(matches):
        name = m.group(2)
        start = m.start(1)  # start of the `def` line (after the \n)
        end = matches[i + 1].start(1) if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        result.append((name, body))
    return result


def _normalise(body: str) -> str:
    """Strip comments, collapse whitespace for similarity comparison."""
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        lines.append(stripped)
    return " ".join(lines)


def _normalise_line_structure(line: str) -> str:
    """Replace string and numeric literals so structurally identical lines compare equal."""
    line = _STR_LIT_RE.sub('""', line)
    line = _NUM_LIT_RE.sub("0", line)
    return line


def _max_line_repeat(text: str) -> tuple[int, str]:
    """Return (max_count, reason) for line-level repetition within a block.

    Checks exact stripped lines first, then structure-normalised lines.
    Returns the higher of the two counts together with the appropriate reason label.
    """
    raw_lines: list[str] = []
    norm_lines: list[str] = []
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


# ── detection ─────────────────────────────────────────────────────────────────


def _mean_pairwise_sim(bodies: list[str]) -> float:
    if len(bodies) < 2:
        return 0.0
    norms = [_normalise(b) for b in bodies]
    sims = [
        SequenceMatcher(None, a, b, autojunk=False).ratio()
        for a, b in combinations(norms, 2)
    ]
    return sum(sims) / len(sims)


def is_repetitive(
    generation: str,
    sim_threshold: float = SIM_THRESHOLD,
    min_funcs: int = MIN_FUNCS,
    line_repeat_min: int = LINE_REPEAT_MIN,
) -> tuple[bool, str | None]:
    """Return (flagged, reason) for a single generation string."""
    blocks = _blocks_from_generation(generation)
    all_fns = []
    for block in blocks:
        all_fns.extend(_extract_functions(block))

    # high pairwise body similarity
    if len(all_fns) >= min_funcs:
        bodies = [body for _, body in all_fns]
        if _mean_pairwise_sim(bodies) >= sim_threshold:
            return True, "high_sim"

    # repeated lines within a block
    for block in blocks:
        count, reason = _max_line_repeat(block)
        if count >= line_repeat_min:
            return True, reason

    return False, None


def audit(
    run_dir: Path,
    sim_threshold: float = SIM_THRESHOLD,
    min_funcs: int = MIN_FUNCS,
    line_repeat_min: int = LINE_REPEAT_MIN,
    show: int = 0,
) -> None:
    gen_file = run_dir / "generations.jsonl"
    if not gen_file.exists():
        sys.exit(f"No generations.jsonl in {run_dir}")

    total = 0
    flagged = 0
    by_reason: Counter = Counter()
    examples = []

    with open(gen_file) as f:
        for raw in f:
            g = json.loads(raw)
            if g.get("group") == "neighborhood":
                continue
            total += 1
            generation = g.get("generation", "")
            hit, reason = is_repetitive(
                generation,
                sim_threshold=sim_threshold,
                min_funcs=min_funcs,
                line_repeat_min=line_repeat_min,
            )
            if hit:
                flagged += 1
                by_reason[reason] += 1
                if show and len(examples) < show:
                    examples.append((reason, g["gen_id"], g.get("group"), generation))

    pct = 100 * flagged / total if total else 0.0
    print(f"Run:      {run_dir.name}")
    print(f"Total:    {total}")
    print(f"Flagged:  {flagged}  ({pct:.1f}%)")
    for reason, count in by_reason.most_common():
        print(f"  {reason:<12} {count:>6}  ({100 * count / total:.1f}%)")

    if examples:
        print()
        for reason, gen_id, group, gen in examples:
            print(f"── example gen_id={gen_id} group={group} reason={reason} ──")
            print(gen)
            print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument(
        "--threshold",
        type=float,
        default=SIM_THRESHOLD,
        help="Mean pairwise similarity to flag high_sim (default 0.7)",
    )
    parser.add_argument(
        "--min-funcs",
        type=int,
        default=MIN_FUNCS,
        help="Min function defs to run similarity check (default 3)",
    )
    parser.add_argument(
        "--line-repeat",
        type=int,
        default=LINE_REPEAT_MIN,
        help="Same (or structurally same) line count to flag (default 5)",
    )
    parser.add_argument("--show", type=int, default=0, help="Print N flagged examples")
    args = parser.parse_args()

    if not args.run_dir.is_dir():
        sys.exit(f"Not a directory: {args.run_dir}")

    audit(
        args.run_dir,
        sim_threshold=args.threshold,
        min_funcs=args.min_funcs,
        line_repeat_min=args.line_repeat,
        show=args.show,
    )
