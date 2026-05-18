# File: edit_presence.py
# Description: Logs edit-presence (EP) metrics and box-plot artifacts for a run directory into MLflow.
# Author: Adam Zvara (xzvara01)
# Date: 05/2026
"""
Each ep_{metric}.json contains:
  n, mean, median, std, q25, q75, min, max  -- logged as MLflow metrics
  values                                     -- used to draw the boxplot

Metrics are logged as:  ep_{metric}_{stat}
  e.g. ep_fully_passing_mean, ep_perplexity_q25, ...

A PNG with multiple subplots is saved under artifacts/edit_presence/:
  - Left panel:       score-based metrics (values roughly in [-1, 1])
  - Separate panels:  one each for perplexity and probabilistic_efficacy
                      (unbounded / different scales)
"""

import json
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow

# Stats to extract and log as metrics
STATS = ("n", "mean", "median", "std", "q25", "q75", "min", "max")

# Display label for each file stem (ep_<stem>.json)
METRIC_LABELS = {
    "fully_passing": "Fully Passing",
    "generation_eval": "Generation Eval",
    "perplexity": "Perplexity",
    "probabilistic_efficacy": "Prob. Efficacy",
    "runnability": "Runnability",
}

# Metrics that live on a different scale — each gets its own individual panel
SEPARATE_SCALE = {"perplexity", "probabilistic_efficacy"}


def _load_ep_files(run_dir: Path) -> dict[str, dict]:
    """Return {metric_name: data_dict} for every ep_*.json found."""
    result = {}
    for path in sorted(run_dir.glob("ep_*.json")):
        metric = path.stem[len("ep_") :]  # strip leading "ep_"
        with open(path) as f:
            result[metric] = json.load(f)
    return result


def _log_metrics(ep_data: dict[str, dict]):
    """Log summary statistics from each ep file as MLflow metrics."""
    for metric, data in ep_data.items():
        for stat in STATS:
            value = data.get(stat)
            if isinstance(value, (int, float)):
                mlflow.log_metric(f"ep_{metric}_{stat}", value)


def _make_bxp_stat(data: dict, label: str) -> dict:
    """Convert an ep data dict to the dict expected by ax.bxp()."""
    return {
        "med": data["median"],
        "q1": data["q25"],
        "q3": data["q75"],
        "whislo": data["min"],
        "whishi": data["max"],
        "mean": data["mean"],
        "fliers": [],
        "label": label,
    }


def _draw_boxes(ax, box_stats: list[dict], colours, zero_line: bool):
    bxp = ax.bxp(
        box_stats,
        showmeans=True,
        meanline=True,
        patch_artist=True,
    )
    for patch, colour in zip(bxp["boxes"], colours):
        patch.set_facecolor(colour)
        patch.set_alpha(0.6)
    if zero_line:
        ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.grid(axis="y", alpha=0.3)
    ax.tick_params(axis="x", rotation=15)


PANEL_TITLES = {
    "score": "Edit Presence — score metrics",
    "perplexity": "Edit Presence — perplexity",
    "probabilistic_efficacy": "Edit Presence — prob. efficacy",
}

PANEL_YLABELS = {
    "score": "Score (Δ edited − baseline)",
    "perplexity": "Perplexity (Δ)",
    "probabilistic_efficacy": "Prob. Efficacy (Δ)",
}


def _build_boxplot(ep_data: dict[str, dict]) -> Path:
    """
    Build a multi-panel boxplot figure and write it to a temp PNG.

    Panel 0:          score-based metrics (roughly [-1, 1]).
    One panel each:   every metric in SEPARATE_SCALE (own axis, own scale).
    If only one panel would be present, a single-panel figure is used.
    """
    score_items = [(m, d) for m, d in ep_data.items() if m not in SEPARATE_SCALE]
    # One panel per separate-scale metric, in deterministic order
    separate_items = [(m, ep_data[m]) for m in sorted(SEPARATE_SCALE) if m in ep_data]

    # Build list of (panel_key, [(metric, data), ...]) for non-empty panels
    panels = []
    if score_items:
        panels.append(("score", score_items))
    for m, d in separate_items:
        panels.append((m, [(m, d)]))

    if not panels:
        return None

    # Width proportional to number of boxes in each panel (min 1)
    widths = [max(1, len(items)) for _, items in panels]
    fig, axes = plt.subplots(
        1,
        len(panels),
        figsize=(sum(w * 1.8 + 1 for w in widths), 5),
        gridspec_kw={"width_ratios": widths},
        squeeze=False,
    )
    axes = axes[0]

    colours = plt.cm.tab10.colors
    colour_offset = 0

    for ax, (panel_key, group) in zip(axes, panels):
        box_stats = [_make_bxp_stat(d, METRIC_LABELS.get(m, m)) for m, d in group]
        _draw_boxes(
            ax, box_stats, colours[colour_offset:], zero_line=(panel_key == "score")
        )
        ax.set_title(PANEL_TITLES.get(panel_key, panel_key), fontsize=12, pad=8)
        ax.set_ylabel(PANEL_YLABELS.get(panel_key, "Value (Δ)"), fontsize=10)
        colour_offset += len(group)

    fig.tight_layout()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        fig.savefig(tmp.name, dpi=150)
        plt.close(fig)
        return Path(tmp.name)


def log_edit_presence(run_dir: Path):
    """
    Discover ep_*.json files in run_dir, log metrics and upload boxplot artifact.
    Does nothing if no ep_* files are present.
    """
    ep_data = _load_ep_files(run_dir)
    if not ep_data:
        return

    _log_metrics(ep_data)

    png_path = _build_boxplot(ep_data)
    if png_path is not None:
        try:
            mlflow.log_artifact(str(png_path), artifact_path="edit_presence")
        finally:
            png_path.unlink(missing_ok=True)

    print(f"    edit_presence: logged {len(ep_data)} metrics + boxplot")
