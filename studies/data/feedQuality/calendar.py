"""The library's calendar deduced from one provider's feeds: holidays, partial closes, outages."""

import numpy as np
import pandas as pd

from engines.market.feed import scale

HOLIDAY, PARTIAL, OUTAGE, OWN = "festivo", "cierre parcial", "caída del proveedor", "símbolo"


def silences(feeds: dict[str, tuple[np.ndarray, np.ndarray]], cfg: dict) -> pd.DataFrame:
    """Stretches in which every feed that should be quoting is silent.

    Args:
        feeds: {feed: (bar minutes, its session mask)} for the provider's feeds.
        cfg: inputs.config()'s dict.

    Returns:
        One row per silence of at least the minimum gap: `start_min`, `end_min`, `minutes`,
        `cls`. A feed counts only between its first and last bar and inside its session.
        A silence that holds a whole weekday with no bar at all is a holiday; else one of
        `partial_close_minutes` or more is a partial close (noted, never marked); shorter,
        a provider outage (marked in every symbol).
    """
    end = max(int(at[-1]) for at, _ in feeds.values()) + 1
    present = np.zeros(end, np.int16)
    live = np.zeros(end, np.int16)
    for at, week_mask in feeds.values():
        present[at] += 1
        span = np.arange(at[0], at[-1] + 1)
        live[span] += week_mask[span % scale.WEEK]
    silent = (live > 0) & (present == 0)
    edges = np.flatnonzero(np.diff(np.r_[0, silent.astype(np.int8), 0]))
    runs = pd.DataFrame({"start_min": edges[::2], "end_min": edges[1::2]})
    runs["minutes"] = runs["end_min"] - runs["start_min"]
    runs = runs[runs["minutes"] >= cfg["gap"]["minutes"]].reset_index(drop=True)

    days = np.arange(end) // 1440
    bars_per_day = np.bincount(days, weights=present, minlength=days[-1] + 1)
    live_per_day = np.bincount(days, weights=live, minlength=days[-1] + 1)
    weekday = (np.arange(len(bars_per_day)) % 7) < 5
    holiday = weekday & (bars_per_day == 0) & (live_per_day > 0)
    held = [holiday[a // 1440:(b - 1) // 1440 + 1].any()
            for a, b in zip(runs["start_min"], runs["end_min"])]
    runs["cls"] = np.where(held, HOLIDAY, np.where(
        runs["minutes"] >= cfg["gap"]["partial_close_minutes"], PARTIAL, OUTAGE))
    runs["t"] = pd.to_datetime((runs["start_min"] + scale.ORIGIN) * scale.MINUTE_NS)
    return runs


def classify(holes: pd.DataFrame, runs: pd.DataFrame) -> pd.Series:
    """Which of one feed's gaps are the whole library's silence, and which are its own.

    Args:
        holes: A feed's gap rows (detect.events(), kind "hueco").
        runs: silences()'s table.

    Returns:
        One class per gap. A gap takes the class of the shared silence it overlaps most
        when shared silences cover at least its in-session missing minutes; any gap longer
        than what everyone shared is the symbol's own.
    """
    a, b = runs["start_min"].to_numpy(), runs["end_min"].to_numpy()
    out = []
    for lo, hi, size in zip(holes["start_min"], holes["end_min"], holes["size"]):
        first, last = np.searchsorted(b, lo, "right"), np.searchsorted(a, hi)
        overlap = np.minimum(b[first:last], hi) - np.maximum(a[first:last], lo)
        shared = overlap.sum() >= size if len(overlap) else False
        out.append(runs["cls"].iloc[first + int(np.argmax(overlap))] if shared else OWN)
    return pd.Series(out, index=holes.index)
