"""The statistic of the travel test: a total in R over any markets and cells, and its z against the random runs."""

from typing import TypedDict, cast

import numpy as np
import pandas as pd

from studies.transfer.crossmarket.travel import tensor


def total(
    values: np.ndarray,
    markets: np.ndarray | list | None = None,
    cells: np.ndarray | list | None = None,
) -> np.ndarray:
    """Sum over a choice of markets and cells, keeping «no data» apart from zero.

    Args:
        values: (..., markets, cells), a tensor's `real`, `null` or `trades`.
        markets, cells: Boolean mask or positions; None takes all.

    Returns:
        The sum over the last two axes of the cells that have data. NaN when none of the
        chosen cells has: a market with no bars in a window has no total there, not 0.
    """
    part = values[..., slice(None) if markets is None else markets, :]
    part = part[..., slice(None) if cells is None else cells]
    return np.where(np.isnan(part).all((-2, -1)), np.nan, np.nansum(part, (-2, -1)))


class Z(TypedDict):
    """A real total against the random totals: z, one-sided p, and the real, mean and sd."""

    z: float
    p: float
    real: float
    mean: float
    sd: float


def z(real: float, null: np.ndarray) -> Z:
    """The real total against the random runs' totals.

    Args:
        real: The real run's total, R.
        null: One total per random run.

    Returns:
        `z` = (real - mean) / sd of the random totals (sd with ddof 1), `p` the one-sided
        empirical p (1 + runs at or above the real) / (runs + 1), and `real`, `mean`, `sd`.
        z and p are NaN when the real total has no data or the random totals do not vary.
    """
    mean, sd = float(np.mean(null)), float(np.std(null, ddof=1))
    live = bool(np.isfinite(real)) and sd > 0
    return Z(
        z=(real - mean) / sd if live else np.nan,
        p=(1 + int((null >= real).sum())) / (null.size + 1) if live else np.nan,
        real=float(real),
        mean=mean,
        sd=sd,
    )


def joint(
    tensor: tensor.Built,
    markets: np.ndarray | list | None = None,
    cells: np.ndarray | list | None = None,
) -> Z:
    """z of one strategy over any markets and cells, from its tensor and nothing else.

    Args:
        tensor: As `tensor.build()` returns it.
        markets, cells: As total() takes them: one market, a family, all but one; one window,
            one year.

    Returns:
        As z() returns it.
    """
    return z(
        cast(float, total(tensor["real"], markets, cells)),
        total(tensor["null"], markets, cells),
    )


def t(values: np.ndarray) -> float:
    """The t of a mean at the AR(1) effective n (annotation only, judges nothing).

    Args:
        values: One observation per week, in time order.

    Returns:
        mean / sd x sqrt(n_eff), n_eff = n (1 - rho) / (1 + rho) capped at n and floored at 2.
        NaN under three observations or without dispersion.
    """
    n = len(values)
    if n < 3 or not np.ptp(values):
        return float("nan")
    x = values - values.mean()
    rho = float((x[1:] * x[:-1]).sum() / (x * x).sum())
    effective = max(min(n * (1 - rho) / (1 + rho), n), 2.0)
    return float(values.mean() / values.std(ddof=1) * np.sqrt(effective))


def weekly(values: np.ndarray, day: np.ndarray) -> pd.Series:
    """One value per trade summed by the week it closed in, weeks ending on Friday.

    Args:
        values: One number per trade.
        day: Each trade's close date, datetime64[D].

    Returns:
        Indexed by each week's Friday, every week from the first to the last present, a week
        with nothing closed at zero (`Series.resample("W-FRI").sum()` in integer arithmetic).
    """
    number = day.astype(np.int64)  # days since 1970-01-01, a Thursday
    friday = number + (1 - number) % 7
    out = np.bincount((friday - friday.min()) // 7, weights=values)
    index = (friday.min() + 7 * np.arange(len(out))).astype("datetime64[D]")
    return pd.Series(out, index=pd.DatetimeIndex(index.astype("datetime64[ns]")))
