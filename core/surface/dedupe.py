"""How many independent observations a parameter grid really holds, and how to resample it."""

from typing import Callable

import numpy as np
import pandas as pd

SENTINEL_LIMIT = 100.0
SENTINEL_COLUMNS = ("RExpectancy",)
IDENTITY = ("NetProfit", "NumberOfTrades")


def drop_sentinels(frame: pd.DataFrame, columns: tuple[str, ...] = SENTINEL_COLUMNS,
                   limit: float = SENTINEL_LIMIT) -> pd.DataFrame:
    """Remove rows whose metric carries SQX's undefined marker instead of a measurement.

    Args:
        frame: One row per grid point.
        columns: Metrics known to carry sentinels. Measured 2026-09-20 on XAUUSD SPP IS:
            `RExpectancy` holds 99999.0 on 3 rows and -1.0 on 15, all of them permutations
            with about one trade.
        limit: Absolute value beyond which a reading is a marker, not a number.

    Returns:
        The frame without those rows. They are 0.08% of the grid and they win the argmax,
        so a ranking that does not drop them is decided by one-trade permutations.
    """
    keep = np.ones(len(frame), dtype=bool)
    for column in columns:
        if column in frame:
            keep &= frame[column].abs() <= limit
    return frame[keep]


def distinct(frame: pd.DataFrame, keys: tuple[str, ...] = IDENTITY) -> pd.DataFrame:
    """One row per grid point that produced a different backtest.

    Args:
        frame: One row per grid point.
        keys: Columns whose pair identifies a result. The default is the one the duplicate
            test uses: two points agreeing on both ran the same backtest.

    Returns:
        The first row of each group. Inert parameters duplicate points -- measured
        2026-09-20, `CBlock_SqzMmnInt21` gave 757 groups and 757 of them agreed on
        NetProfit and trade count to the last decimal -- so a statistic over rows counts
        the same backtest many times.
    """
    return frame.drop_duplicates(subset=list(keys))


def n_eff(frame: pd.DataFrame, keys: tuple[str, ...] = IDENTITY) -> int:
    """Grid points with a distinct result.

    Args:
        frame: One row per grid point.
        keys: Columns whose pair identifies a result.

    Returns:
        The count every interval and every noise threshold must be fed, in place of the
        row count. A confidence interval computed over correlated rows is falsely narrow
        by roughly a factor of three at this grid's autocorrelation.
    """
    return int(len(distinct(frame, keys)))


def bootstrap_ci(values: np.ndarray, statistic: Callable[[np.ndarray], float],
                 n_resamples: int = 9999, confidence: float = 0.95,
                 seed: int = 0) -> tuple[float, float]:
    """Percentile bootstrap interval, resampling the values it is given and nothing else.

    Args:
        values: One entry per **distinct tuple**, never one per row. Pass the output of
            `distinct` -- resampling rows would resample the same backtest repeatedly and
            report an interval the data does not support.
        statistic: Maps a resample to one number.
        n_resamples: Draws.
        confidence: Coverage of the returned interval.
        seed: Fixes the draw, so a report regenerated tomorrow gives the same interval.

    Returns:
        (low, high) at the requested coverage.
    """
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, values.size, size=(n_resamples, values.size))
    spread = np.array([statistic(values[row]) for row in draws])
    tail = (1 - confidence) / 2
    return float(np.quantile(spread, tail)), float(np.quantile(spread, 1 - tail))
