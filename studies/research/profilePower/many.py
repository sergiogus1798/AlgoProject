"""The replications judged: detection per planted effect, and the minimum detectable effect."""

import numpy as np
import pandas as pd

from studies.research.marketProfile import many as profile_many


def judged(runs: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Every replication with its verdicts.

    Args:
        runs: One row per replication (one.run).
        cfg: The parsed config; the three filters after significance are the profile's own.

    Returns:
        runs plus `p`, `significant` (the full count of draws reached and p within the cut),
        `single` (the first chunk alone at `single_level`: the rule judged as the only test),
        `pays`, `stable`, `frequent` — the profile's thresholds — and `passes`, all four.
    """
    filters, judge = cfg["profile"]["filters"], cfg["judge"]
    out = runs.copy()
    out["p"] = (1 + out["exceed"]) / (out["drawn"] + 1)
    out["significant"] = (out["drawn"] >= out["draws"]) & (out["p"] <= judge["cut"] * (1 + 1e-9))
    out["single"] = out["p_first"] <= judge["single_level"]
    out["pays"] = out["multiple"].fillna(-np.inf) >= filters["cost_multiple"]
    out["stable"] = (out["years_with_sign"] / out["years"]).fillna(0) > filters["stable_share"]
    out["frequent"] = out["trades_per_year"] >= profile_many.min_trades(out["symbol"], filters)
    out["passes"] = out["significant"] & out["pays"] & out["stable"] & out["frequent"]
    return out


def curve(runs: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """The power curve: per group and planted effect, how often each verdict was reached.

    Args:
        runs: What judged() returned.
        by: Grouping columns, e.g. ["family", "measure", "timeframe"].

    Returns:
        One row per group and effect: `runs`, the rates `significant`, `passes`, `single`,
        `frequent`, the mean realised `multiple` and the mean `trades_per_year`.
    """
    return runs.groupby([*by, "effect_planted"], sort=True).agg(
        runs=("significant", "size"), significant=("significant", "mean"),
        passes=("passes", "mean"), single=("single", "mean"), frequent=("frequent", "mean"),
        multiple=("multiple", "mean"), trades_per_year=("trades_per_year", "mean")).reset_index()


def crossing(effects: np.ndarray, rates: np.ndarray, target: float) -> float:
    """The first effect at which a rate reaches `target`, read on the line between grid points.

    Returns:
        NaN when the rate never reaches it on the grid: the minimum is beyond the largest
        effect planted.
    """
    above = np.flatnonzero(rates >= target)
    if above.size == 0:
        return np.nan
    k = above[0]
    if k == 0:
        return float(effects[0])
    return float(np.interp(target, rates[k - 1:k + 1], effects[k - 1:k + 1]))


def minimum(table: pd.DataFrame, by: list[str], target: float) -> pd.DataFrame:
    """The minimum detectable effect of each group, under each verdict.

    Args:
        table: What curve() returned.
        by: The grouping columns it was built with.
        target: The detection rate asked for.

    Returns:
        One row per group: `mde_significant`, `mde_passes`, `mde_single` in round-trip costs
        (NaN: not reached at the largest effect), the false alarm rates at no effect, the
        detection at the largest effect, and the trades a year.
    """
    rows = []
    for key, part in table.groupby(by, sort=True):
        part = part.sort_values("effect_planted")
        x, none = part["effect_planted"].to_numpy(), part.iloc[0]
        rows.append({**dict(zip(by, key if isinstance(key, tuple) else (key,))),
                     "runs": int(part["runs"].sum()),
                     "trades_per_year": part["trades_per_year"].mean(),
                     **{f"mde_{v}": crossing(x, part[v].to_numpy(), target)
                        for v in ("significant", "passes", "single")},
                     "alarm_significant": none["significant"], "alarm_single": none["single"],
                     "top_significant": part.iloc[-1]["significant"],
                     "top_passes": part.iloc[-1]["passes"]})
    return pd.DataFrame(rows)
