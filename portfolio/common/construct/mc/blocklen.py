"""How long the resampled blocks are: measured on the combination's own daily P&L, plus a sweep."""

import numpy as np
import pandas as pd

from engines.inference.snooping import superior


def daily_pnl(days: dict[str, np.ndarray]) -> np.ndarray:
    """Mark-to-market P&L per server day of a joint day table: closed plus the change in floating."""
    floating = np.asarray(days["float_end"], dtype=float)
    return np.asarray(days["closed"], dtype=float) + np.diff(floating, prepend=0.0)


def lengths(days: dict[str, np.ndarray], sweep: list[int]) -> dict:
    """The block lengths a combination is resampled at.

    Args:
        days: The combination's joint server days ([D] arrays).
        sweep: The fixed lengths every combination is also read at, in server days.

    Returns:
        `measured` (Politis and White's optimal mean length of the stationary bootstrap on the
        daily P&L, at least 1) and `lengths` (the sweep and the measured one, sorted, each
        once). Which one decides is the caller's rule, not chosen here.
    """
    measured = superior.block_length(pd.DataFrame({"pnl": daily_pnl(days)}))
    return {"measured": measured, "lengths": sorted({*sweep, measured})}
