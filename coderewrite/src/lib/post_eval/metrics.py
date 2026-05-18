# File: metrics.py
# Description: Provides box-plot statistical summary helpers for edit-presence (EP) distributions.
# Author: Adam Zvara (xzvara01)
# Date: 04/2026


import statistics


def box_stats(values: list[float]) -> dict:
    """Compute box-plot statistics for a list of EP values.

    Returns a dict suitable for direct JSON serialisation:

        {
            "n": int,
            "mean": float,
            "median": float,
            "std": float,        # sample std (0.0 when n == 1)
            "q25": float,        # first quartile
            "q75": float,        # third quartile
            "min": float,
            "max": float,
            "values": [float, ...]
        }

    Returns an empty-result dict (all scalars None) when *values* is empty.
    """
    if not values:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "q25": None,
            "q75": None,
            "min": None,
            "max": None,
            "values": [],
        }

    n = len(values)
    q25, _, q75 = statistics.quantiles(values, n=4)
    return {
        "n": n,
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "std": statistics.stdev(values) if n > 1 else 0.0,
        "q25": q25,
        "q75": q75,
        "min": min(values),
        "max": max(values),
        "values": list(values),
    }
