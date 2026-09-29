"""How many independent observations a parameter grid really holds, and how to resample it;
plus the one exact test for two strategies sharing one trade list under different names."""

import hashlib
from typing import Callable

import numpy as np
import pandas as pd

SENTINEL_LIMIT = 100.0
SENTINEL_COLUMNS = ("RExpectancy",)
IDENTITY = ("NetProfit", "NumberOfTrades")
TRADE_COLUMNS = ("Open time", "Close time", "Profit/Loss")


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


def trade_duplicates(trades: pd.DataFrame, by: str,
                     columns: tuple[str, ...] = TRADE_COLUMNS) -> pd.Series:
    """Which strategies of a trade export are the same trade list under a different identity.

    Args:
        trades: Trades of possibly many strategies, one row per trade, carrying `by` and
            `columns`.
        by: Column naming which strategy each row belongs to.
        columns: Trade fields that decide identity. The default three are enough: two
            strategies agreeing on every open time, close time and P/L of every trade ran
            the same backtest, whatever their name or `.sqx` hash says (`studies/CLAUDE.md`'s
            first trap -- 45 of 231 strategies once shared trades under different hashes).

    Returns:
        One bool per value of `by`, indexed by it: True for every member of a duplicate
        group but its first. A strategy with zero trades reads False, not a false clone.
    """
    fingerprint = pd.util.hash_pandas_object(trades[list(columns)], index=False)
    key = fingerprint.groupby(trades[by].values, observed=True).sum()
    return key.duplicated(keep="first") & key.notna()


def curve_duplicates(curves: dict[str, pd.Series]) -> pd.Series:
    """Which strategies share another one's daily equity curve, values and dates alike.

    Args:
        curves: {strategy name: daily cumulative P&L}, e.g. from `core.sqxstats.equity`.

    Returns:
        One bool per name: True for every member of a duplicate group but its first. Two
        strategies agreeing on every day's P&L ran the same trades -- a curve carries no
        less information than the list that produced it, and hashing it needs no export
        `trade_duplicates` would (`studies/CLAUDE.md`'s dedup trap). `hashlib`, not the
        builtin `hash()`, because Python salts a bytes hash per process: the same input
        would group differently in a report regenerated tomorrow.
    """
    key = pd.Series({name: hashlib.sha1(curve.to_numpy().tobytes()).digest()
                     for name, curve in curves.items()})
    return key.duplicated(keep="first")
