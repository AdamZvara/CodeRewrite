#!/usr/bin/env python3
"""Compute edit-presence (EP) comparative metrics.

Compares a baseline run directory against one or more edited runs and writes
EP metric files (``ep_*.json``) into each target run directory.

Single-pair mode
----------------
    python -m src.scripts.run_post_eval \\
      --baseline results/exp/20240315_BASELINE_qwen/ \\
      --target   results/exp/20240316_KE_qwen_ROME_edit_single/

Batch mode (whole experiment directory)
---------------------------------------
    python -m src.scripts.run_post_eval --runs-dir results/rectangle_area/

In batch mode the baseline run is identified by ``"type": "BASELINE"`` in
``parameters.json``.  Pass ``--baseline`` explicitly to override.
"""

import argparse
import json
import sys
from pathlib import Path

from ..lib.post_eval.compare import RunComparison


def _find_baseline(runs_dir: Path) -> Path:
    candidates = []
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        params_file = d / "parameters.json"
        if not params_file.exists():
            continue
        params = json.loads(params_file.read_text())
        if params.get("type") == "BASELINE":
            candidates.append(d)
    if not candidates:
        raise SystemExit(f"Error: no BASELINE run found in {runs_dir}")
    if len(candidates) > 1:
        print(
            f"Warning: multiple BASELINE runs found, using most recent: {candidates[-1].name}",
            file=sys.stderr,
        )
    return candidates[-1]


def _process_single(baseline_dir: Path, target_dir: Path) -> None:
    comp = RunComparison(baseline_dir, target_dir)
    results = comp.compute()
    comp.write(results)
    written = [f"ep_{m}.json" for m, v in results.items() if v is not None]
    print(f"Wrote {len(written)} EP file(s) to {target_dir}: {', '.join(written)}")


def _process_batch(runs_dir: Path, baseline_dir: Path | None) -> None:
    if baseline_dir is None:
        baseline_dir = _find_baseline(runs_dir)
    print(f"Baseline: {baseline_dir.name}")

    processed = 0
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir() or d.resolve() == baseline_dir.resolve():
            continue
        if not (d / "parameters.json").exists():
            continue
        try:
            _process_single(baseline_dir, d)
            processed += 1
        except Exception as exc:
            print(f"  Skipped {d.name}: {exc}", file=sys.stderr)

    print(f"Done — processed {processed} run(s).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute edit-presence (EP) comparative metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--target",
        type=Path,
        metavar="DIR",
        help="Single edited run directory (requires --baseline)",
    )
    mode.add_argument(
        "--runs-dir",
        type=Path,
        metavar="DIR",
        help="Directory containing multiple run subdirectories (batch mode)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        metavar="DIR",
        help="Baseline run directory (required with --target; "
        "auto-detected with --runs-dir)",
    )

    args = parser.parse_args()

    if args.target:
        if not args.baseline:
            parser.error("--baseline is required when using --target")
        _process_single(args.baseline, args.target)
    else:
        _process_batch(args.runs_dir, args.baseline)


if __name__ == "__main__":
    main()
