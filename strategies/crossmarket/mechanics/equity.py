"""Equity on the calendar, for the real run and for the cone of random ones around it."""

import numpy as np
import pandas as pd


def bin_of(bar: np.ndarray, n_bars: int, steps: int) -> np.ndarray:
    """Which time step a bar index falls in.

    Args:
        bar: Bar indices.
        n_bars: Bars in the market.
        steps: Steps the sample is cut into.

    Returns:
        A step index per bar. Bars are evenly spaced in market time, so equal counts of
        bars are equal stretches of trading — which is the axis a reader means by "when".
    """
    return np.minimum((bar * steps) // n_bars, steps - 1)


def path(pnl: np.ndarray, closed: np.ndarray, n_bars: int, steps: int,
         equity0: float) -> np.ndarray:
    """Equity through the sample for a batch of runs, one point per time step.

    Args:
        pnl: One row per run, one column per trade, in USD, zero where not a trade.
        closed: Same shape, the bar index each trade closed on.
        n_bars: Bars in the market.
        steps: Points per curve.
        equity0: Starting account in USD.

    Returns:
        A (runs, steps) array. Each trade's P&L lands in the step its **exit** falls in,
        because that is when the money is realised; the steps are then accumulated. Random
        runs place their trades at different times, so this — not the trade number — is the
        axis on which a random curve and the real one can be laid over each other.
    """
    step = bin_of(closed, n_bars, steps)
    rows = np.repeat(np.arange(pnl.shape[0]), pnl.shape[1])
    totals = np.zeros((pnl.shape[0], steps))
    np.add.at(totals, (rows, step.ravel()), pnl.ravel())
    return equity0 + np.cumsum(totals, axis=1)


def bands(curves: np.ndarray, qs: list[float]) -> dict:
    """Percentile bands across a batch of equity curves.

    Args:
        curves: What path() returned for the random runs.
        qs: Percentiles to band, low to high.

    Returns:
        {percentile: one curve}. Read the cone for its width, not for any single line
        inside it: the cone is what the same trading rhythm laid down at random times could
        have produced.
    """
    return {q: row.tolist() for q, row in zip(qs, np.percentile(curves, qs, axis=0))}


def dates(bars: pd.DataFrame, steps: int) -> list[str]:
    """The date at the end of each time step, for the axis.

    Args:
        bars: One market's bars.
        steps: Points per curve.

    Returns:
        One ISO date per step.
    """
    edges = np.minimum((np.arange(1, steps + 1) * len(bars)) // steps, len(bars) - 1)
    return [str(bars.index[i].date()) for i in edges]
