"""Cost and execution robustness: how much of the edge survives worse fills or a bigger spread."""

import numpy as np
import pandas as pd

from strategies.crossmarket import pricing

DEFAULT_MULTIPLES = [1.0, 1.5, 2.0, 2.5, 3.0]


def cost_gradient(fixed: dict, bars: pd.DataFrame, multiples: list[float] = DEFAULT_MULTIPLES
                  ) -> pd.DataFrame:
    """Mean net return at each cost multiple.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        multiples: Cost multipliers to evaluate.

    Returns:
        Columns multiple and mean_return. Linear in the multiple, since gross return per
        trade does not depend on the cost assumption.
    """
    gross = pricing.realised(bars, fixed["held"], fixed["fill"]["convention"])
    mean_gross = float(gross.mean())
    return pd.DataFrame({"multiple": multiples,
                         "mean_return": [mean_gross - m * fixed["cost"] for m in multiples]})


def breakeven_multiple(fixed: dict, bars: pd.DataFrame) -> float:
    """The cost multiple at which the mean net return crosses zero.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.

    Returns:
        mean(gross) / cost. Closed form because the net return is linear in the multiple.
        The PDF's gate requires this at or above 2x.
    """
    gross = pricing.realised(bars, fixed["held"], fixed["fill"]["convention"])
    return float(gross.mean() / fixed["cost"])


def bar_shift_stress(fixed: dict, bars: pd.DataFrame, shift: int) -> float:
    """Decay in mean return when entry and exit are moved by a fixed number of bars.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        shift: Bars to move both entry and exit by.

    Returns:
        Fractional change in mean net return versus the real trades: negative means decay.
        Trades whose shifted entry or exit would fall outside the bar file are dropped.
    """
    held = fixed["held"]
    entry, exit_ = held["entry"].to_numpy() + shift, held["exit"].to_numpy() + shift
    keep = (entry >= 0) & (exit_ < len(bars))
    enter_col, leave_col = pricing.CONVENTIONS[fixed["fill"]["convention"]]
    shifted = (np.log(bars[leave_col].to_numpy()[exit_[keep]]
                      / bars[enter_col].to_numpy()[entry[keep]]) - fixed["cost"])
    real = pricing.realised(bars, held, fixed["fill"]["convention"])[keep] - fixed["cost"]
    return float(shifted.mean() / real.mean() - 1)


def range_slippage_stress(fixed: dict, bars: pd.DataFrame, fraction: float) -> float:
    """Decay in mean return when entries and exits slip against the position.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        fraction: Share of the bar's High-Low range added against the trade at both ends.

    Returns:
        Fractional change in mean net return versus the real trades. Long-only: entry moves
        up by fraction * range, exit moves down by fraction * range of its own bar.
    """
    held = fixed["held"]
    entry_range = (bars["High"] - bars["Low"]).to_numpy()[held["entry"].to_numpy()]
    exit_range = (bars["High"] - bars["Low"]).to_numpy()[held["exit"].to_numpy()]
    enter_col, leave_col = pricing.CONVENTIONS[fixed["fill"]["convention"]]
    enter_px = bars[enter_col].to_numpy()[held["entry"].to_numpy()] + fraction * entry_range
    leave_px = bars[leave_col].to_numpy()[held["exit"].to_numpy()] - fraction * exit_range
    slipped = np.log(leave_px / enter_px) - fixed["cost"]
    real = pricing.realised(bars, held, fixed["fill"]["convention"]) - fixed["cost"]
    return float(slipped.mean() / real.mean() - 1)
