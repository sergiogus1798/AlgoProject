"""Data quality (spec 6.6): how much of the edge lives in trades that touch a feed anomaly."""

import numpy as np
import pandas as pd

from engines.market.feed import scale

FACTS = ("ret_datos", "t_a", "n_afectadas")


def mark(oos: pd.DataFrame, index: pd.DatetimeIndex, width: int, ev: pd.DataFrame,
         skip_cls: tuple = ()) -> np.ndarray:
    """Which trades have an anomaly between their entry bar and their exit bar, both included.

    Args:
        oos: The per-trade table (`open_time`, `close_time`), naive on the feed's clock.
        index: Open times of the strategies' bars.
        width: Bar width in minutes.
        ev: The feed's events.parquet (`start_min`, `end_min` half-open, `cls`), same clock.
        skip_cls: Anomaly classes that do not count; empty = every event counts.

    Returns:
        Boolean per trade. Events may overlap: they are merged through a running maximum
        of their ends, so a trade is hit when the latest-starting event before its window's
        end reaches into the window.
    """
    ev = pd.DataFrame(ev[~ev["cls"].isin(list(skip_cls))]).sort_values("start_min")
    starts, ends = ev["start_min"].to_numpy(), np.maximum.accumulate(ev["end_min"].to_numpy())
    at = scale.minutes(index)
    k = np.clip(np.searchsorted(index, oos["open_time"].to_numpy(), "right") - 1, 0, None)
    j = np.clip(np.searchsorted(index, oos["close_time"].to_numpy(), "right") - 1, 0, None)
    a, b = at[k], at[j] + width
    last = np.searchsorted(starts, b, "left") - 1
    return (last >= 0) & (ends[np.maximum(last, 0)] > a)


def facts(oos: pd.DataFrame, affected: np.ndarray) -> pd.DataFrame:
    """`ret_datos`, `t_a` and `n_afectadas` per identity.

    Args:
        oos: The per-trade table with `identity` and `excess` (never recomputed here).
        affected: mark() of the same rows.

    Returns:
        Indexed by identity. `ret_datos` = mean excess without the affected / mean excess of
        all, NaN when that mean is not positive; `t_a` = Welch t of affected minus the rest,
        NaN with fewer than two trades in either group.
    """
    d = pd.DataFrame({"identity": oos["identity"].to_numpy(), "e": oos["excess"].to_numpy(),
                      "a": affected})
    d["e_a"], d["e_r"] = d["e"].where(d["a"]), d["e"].where(~d["a"])
    g = d.groupby("identity", sort=False)
    n_a = pd.Series(g["a"].sum())
    n_r = pd.Series(g["a"].count()) - n_a
    mean = pd.Series(g["e"].mean())
    e_a, e_r = pd.Series(g["e_a"].mean()), pd.Series(g["e_r"].mean())
    ret = (e_r / mean).where(mean > 0)
    ret[n_a == 0] = np.where(mean[n_a == 0] > 0, 1.0, np.nan)   # nothing removed: all of it kept
    se = np.sqrt(pd.Series(g["e_a"].var()) / n_a + pd.Series(g["e_r"].var()) / n_r)
    t = ((e_a - e_r) / se).where((n_a >= 2) & (n_r >= 2))
    return pd.DataFrame({"ret_datos": ret, "t_a": t, "n_afectadas": n_a.astype(float)})
