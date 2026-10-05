"""A combination's daily path on one calendar segment, at the weights `build` gave it (the verdicts read it)."""

import numpy as np
import pandas as pd

from portfolio.common.construct import weights
from portfolio.common.construct.equity import matrix


def paths(daily: pd.DataFrame, calendar: dict, scale: np.ndarray, members: np.ndarray,
          cfg: dict, segment: str) -> tuple[np.ndarray, pd.DatetimeIndex]:
    """Combinations' daily P&L per unit of risk on one segment, at the weights build gave them.

    Args:
        daily: The universe's daily P&L, one column per member.
        calendar: The portfolio calendar, naive Timestamps.
        scale: [N] each member's fixed-risk factor.
        cfg: The construct config.
        members: bool [P, N] over `daily`'s columns.
        segment: The calendar segment to read; only its rows are touched.

    Returns:
        [P, D] paths and the segment's D days.
    """
    build_daily = matrix.segment(daily, calendar, "build")
    rows = matrix.segment(daily, calendar, segment)
    held = weights.matrix(build_daily.fillna(0.0) * scale, members, cfg)
    return held @ (np.nan_to_num(rows.to_numpy().T) * scale[:, None]), rows.index
