"""The normal approximation of the profile's power: what a t statistic can see, from its error."""

from collections.abc import Sequence
from typing import Any, cast

import pandas as pd
from scipy.stats import norm


def error(rows: pd.DataFrame) -> pd.Series:
    """The standard error of a measure's mean gain per trade, in round-trip costs.

    Args:
        rows: Measure rows with `multiple` (mean gain over cost), `stat` (the t of the trades)
            and `null_sd` (the spread of that t under the null).

    Returns:
        multiple / stat is the error a t statistic implies; `null_sd` widens it by what the
        null says the t really spreads — above one where trades overlap. NaN where the
        measure was not tested (a t of exactly zero).
    """
    stat = rows["stat"].where(rows["stat"] != 0)
    return (rows["multiple"] / stat).abs() * rows["null_sd"]


def power(effect: pd.Series | float, se: pd.Series, cut: float) -> pd.Series:
    """The chance a one-sided test at raw p `cut` names an excess of `effect` costs."""
    return pd.Series(norm.cdf(effect / se - norm.isf(cut)), index=se.index).where(
        se.notna()
    )


def detectable(se: pd.Series, cut: float, target: float) -> pd.Series:
    """The smallest excess, in costs, named with probability `target` at raw p `cut`."""
    return cast("pd.Series", (norm.isf(cut) + norm.ppf(target)) * se)


def calibrated(runs: pd.DataFrame, cut: float, hit: list[str]) -> pd.DataFrame:
    """The approximation against the simulation, per measure, timeframe and planted effect.

    Args:
        runs: What many.judged() returned.
        cut: The raw p of the test.
        hit: Measures whose statistic is a hit rate: the approximation does not cover them.

    Returns:
        `detected` (simulated rate) beside `predicted` (mean of power() over the same
        replications, each at its own realised error), and their difference.
    """
    rows = pd.DataFrame(runs[~runs["measure"].isin(hit)])
    rows = rows.assign(
        predicted=power(pd.Series(rows["effect_planted"]), error(rows), cut)
    )
    out = (
        rows.groupby(["measure", "timeframe", "effect_planted"], sort=False)
        .agg(
            runs=("significant", "size"),
            detected=("significant", "mean"),
            predicted=("predicted", "mean"),
        )
        .reset_index()
    )
    return out.assign(gap=out["detected"] - out["predicted"])


def widened(
    measures: pd.DataFrame,
    context: pd.DataFrame,
    classes: dict,
    cut: float,
    target: float,
    hit: list[str],
) -> pd.DataFrame:
    """Every trade measure of the map with the smallest excess it could have named.

    Args:
        measures: The profile's `measures.csv`.
        context: Its `context.csv` (cost over ATR per cell).
        classes: Asset to asset class.
        cut: The raw p the map's correction demands.
        target: The power the minimum is read at.
        hit: Measures whose statistic is a hit rate, left out: their t is not in the map.

    Returns:
        The tested trade rows that need no clock and are judged by a t, plus `asset_class`, `mde` (round-trip
        costs, excess over what the null's drift already gives) and `mde_atr` (the same in
        ATRs of the cell's bar).
    """
    rows = pd.DataFrame(
        measures[
            measures["n_trades"].notna()
            & ~measures["needs_clock"]
            & (measures["stat"] != 0)
            & ~measures["measure"].isin(hit)
        ]
    ).copy()
    rows["asset_class"] = rows["symbol"].map(cast("Any", classes))
    rows["mde"] = detectable(error(rows), cut, target)
    ratio = context.set_index(["symbol", "timeframe"])["cost_over_atr"]
    rows["mde_atr"] = (
        rows["mde"]
        * ratio.reindex(
            pd.MultiIndex.from_frame(pd.DataFrame(rows[["symbol", "timeframe"]]))
        ).to_numpy()
    )
    return rows


def reachable(
    rows: pd.DataFrame, by: list[str], levels: Sequence[float]
) -> pd.DataFrame:
    """Per group, the median detectable excess and the share of tests that can see each level.

    Args:
        rows: What widened() returned.
        by: Grouping columns.
        levels: Effects in costs, e.g. [1, 2, 5].
    """
    out = (
        rows.groupby(by, sort=True)
        .agg(
            tests=("mde", "size"),
            mde_median=("mde", "median"),
            mde_atr_median=("mde_atr", "median"),
            trades_per_year_median=("trades_per_year", "median"),
        )
        .reset_index()
    )
    for level in levels:
        share = rows.assign(ok=rows["mde"] <= level).groupby(by, sort=True)["ok"].mean()
        out[f"sees_{level:g}x"] = share.to_numpy()
    return out
