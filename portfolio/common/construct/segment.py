"""A combination's daily path on one calendar segment, at the weights `build` gave it (the verdicts read it)."""

import numpy as np
import pandas as pd

from portfolio.common.construct import weights
from portfolio.common.construct.equity import matrix


def held(
    daily: pd.DataFrame,
    calendar: dict,
    scale: np.ndarray,
    members: np.ndarray,
    cfg: dict,
) -> np.ndarray:
    """The weights `build` gives each combination -- build rows only, scaled: the ones the verdicts judge.

    Returns:
        float [P, N], `weights.matrix`'s, over `daily`'s columns.
    """
    build_daily = matrix.segment(daily, calendar, "build")
    return weights.matrix(build_daily.fillna(0.0) * scale, members, cfg)


def paths(
    daily: pd.DataFrame,
    calendar: dict,
    scale: np.ndarray,
    members: np.ndarray,
    cfg: dict,
    segment: str,
) -> tuple[np.ndarray, pd.DatetimeIndex]:
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
    rows = matrix.segment(daily, calendar, segment)
    return held(daily, calendar, scale, members, cfg) @ (
        np.nan_to_num(rows.to_numpy().T) * scale[:, None]
    ), pd.DatetimeIndex(rows.index)
