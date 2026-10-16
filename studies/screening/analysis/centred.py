"""What the gate reads against its own population's centre: the change of trading rate from the build to oos1, the slope of a per-trade column in time."""

from typing import cast

import numpy as np
import pandas as pd

from core import metrics

YEAR = metrics.YEAR_DAYS


def calendar_exposure(first: pd.Timestamp, last: pd.Timestamp) -> pd.Series:
    """How much of each calendar year a window covers.

    Returns:
        Indexed by every calendar year from `first` to `last`: the years of it inside the window
        (1.0 for a whole one, less for the two at the edges).
    """
    years = range(first.year, last.year + 1)
    year = cast(pd.Timedelta, pd.Timedelta(days=YEAR))
    return pd.Series(
        [
            cast(
                pd.Timedelta,
                min(last, pd.Timestamp(y + 1, 1, 1))
                - max(first, pd.Timestamp(y, 1, 1)),
            )
            / year
            for y in years
        ],
        index=list(years),
    )


def dispersion(
    counts: pd.DataFrame, exposure: pd.Series, low: float, high: float
) -> pd.Series:
    """The overdispersion of each strategy's yearly trade counts against a Poisson, bounded.

    Args:
        counts: One row per strategy, one column per calendar year, zeros included.
        exposure: calendar_exposure() of the same years.
        low, high: The bounds of the result.

    Returns:
        Pearson's chi-square of the counts against rate x exposure, over years - 1: with whole
        years it is the counts' variance over their mean. A part year is expected to hold its
        share, so it does not read as dispersion.
    """
    width = exposure.to_numpy()
    expected = np.outer(counts.sum(axis=1) / width.sum(), width)
    with np.errstate(divide="ignore", invalid="ignore"):
        chi = np.nansum((counts.to_numpy() - expected) ** 2 / expected, axis=1)
    return pd.Series(chi / (len(width) - 1), index=counts.index).clip(low, high)


def rate_change(
    n_build: pd.Series,
    years_build: float,
    n_oos: pd.Series,
    years_oos: float,
    phi: pd.Series,
) -> pd.DataFrame:
    """The log of the ratio of trading rates, oos1 over build, and its standard error.

    Args:
        n_build, n_oos: Trades per strategy in each window.
        years_build, years_oos: The windows' lengths.
        phi: dispersion() per strategy.

    Returns:
        `log_rate` = ln((n_oos / years_oos) / (n_build / years_build)) and `se` =
        sqrt(phi x (1 / n_build + 1 / n_oos)), the Poisson error widened by phi. Empty where a
        window has no trade.
    """
    both = (n_build > 0) & (n_oos > 0)
    n_build, n_oos = n_build.where(both), n_oos.where(both)
    return pd.DataFrame(
        {
            "log_rate": np.log((n_oos / years_oos) / (n_build / years_build)),
            "se": np.sqrt(phi * (1 / n_build + 1 / n_oos)),
        }
    )


def centre(
    values: pd.Series, group: pd.Series, min_strategies: int, cap: float | None
) -> pd.Series:
    """What the population a strategy belongs to did, to be subtracted from its own value.

    Args:
        values: One figure per strategy.
        group: The population of each: same asset, timeframe and side.
        min_strategies: A population with fewer values is not a reference: its centre is 0.
        cap: The centre is held within +-cap, so that a population that moved as one keeps
            what exceeds it in each strategy's own figure. None = no cap.

    Returns:
        Per strategy, the median of its population's values, capped.
    """
    by = values.groupby(group.reindex(values.index))
    median = pd.Series(by.transform("median"))
    if cap is not None:
        median = median.clip(-cap, cap)
    return median.where(pd.Series(by.transform("count")) >= min_strategies, 0.0)


def slope(trades: pd.DataFrame, value: str, years: np.ndarray) -> pd.DataFrame:
    """The least-squares slope of one per-trade column against time, per strategy.

    Args:
        trades: One sample's trades, already in time order within each `identity`.
        value: The column regressed, in account currency.
        years: When each trade counts, in years from any common origin.

    Returns:
        Indexed by identity: `n`; `b`, the column's change per year; `se`, its standard error
        at the residuals' AR(1) effective n — tradelevel.t()'s: n(1 - rho) / (1 + rho), capped
        at n and floored at 2; and `mean`, the column's mean, which is the fitted value at the
        trades' mean time. `se` is empty under three trades.
    """
    key = trades["identity"].to_numpy()
    frame = pd.DataFrame(
        {"x": np.asarray(years, dtype=float), "y": trades[value].to_numpy()}
    )
    by = frame.groupby(key, sort=False)
    n, mean = by.size(), by.mean()
    d = frame - by.transform("mean")
    moments = pd.DataFrame({"xx": d["x"] ** 2, "xy": d["x"] * d["y"]}).groupby(
        key, sort=False
    )
    b = pd.Series(moments["xy"].sum()) / pd.Series(moments["xx"].sum())
    r = (
        d["y"]
        - pd.Series(moments["xy"].transform("sum"))
        / pd.Series(moments["xx"].transform("sum"))
        * d["x"]
    ).to_numpy()
    lagged = np.where(np.r_[False, key[1:] == key[:-1]], r * np.r_[0.0, r[:-1]], 0.0)
    sums = pd.DataFrame({"g0": r * r, "g1": lagged}).groupby(key, sort=False).sum()
    rho = sums["g1"] / sums["g0"]
    effective = pd.Series(np.minimum(n * (1 - rho) / (1 + rho), n)).clip(lower=2)
    variance = pd.Series(sums["g0"] / (n - 2) / moments["xx"].sum()).where(n > 2)
    return pd.DataFrame(
        {"n": n, "b": b, "se": np.sqrt(variance * n / effective), "mean": mean["y"]}
    )
