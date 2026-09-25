"""The shape of one parameter's curve: where it peaks, how wide the flat part is, where to centre."""

import numpy as np
import pandas as pd


def marginal(frame: pd.DataFrame, parameter: str, metric: str) -> pd.DataFrame:
    """One row per level of a parameter, summarising every tuple that used it.

    Args:
        frame: A grid, parameters and metrics side by side.
        parameter: The column to profile.
        metric: The column to summarise.

    Returns:
        Level, median, interquartile range and count, sorted by level. The median and not
        the mean: these metrics are heavy-tailed and one blow-up tuple moves a mean a long
        way. The count matters because an SPP samples, so the levels are not equally
        represented and a sparse level's median is a weaker reading.
    """
    grouped = frame.groupby(parameter)[metric]
    return pd.DataFrame({
        "level": grouped.median().index,
        "median": grouped.median().to_numpy(),
        "iqr": (grouped.quantile(0.75) - grouped.quantile(0.25)).to_numpy(),
        "n": grouped.size().to_numpy()}).sort_values("level").reset_index(drop=True)


def plateau(profile: pd.DataFrame, share: float = 0.5) -> dict:
    """The contiguous run of levels that stays near the top of the curve.

    Args:
        profile: Output of `marginal`.
        share: How far below the best level a level may sit and still count, as a share of
            the range between the best and the worst level.

    Returns:
        The plateau's first and last level, its width in levels, and its centre. The centre
        is the midpoint of the stable run, **not the argmax** -- which is what SQX's own
        `BestValue` does, and it coincides with the argmax on only five to nine of each
        strategy's parameters.

        Contiguity is the point. A set of good-but-scattered levels is not a plateau: a
        design centred on it would sit next to levels that fail, and a parameter that has
        to be hit exactly is not one you can deploy.
    """
    value = profile["median"].to_numpy()
    floor = value.max() - share * (value.max() - value.min())
    good = value >= floor
    best = int(np.argmax(value))
    lo = hi = best
    while lo > 0 and good[lo - 1]:
        lo -= 1
    while hi < len(good) - 1 and good[hi + 1]:
        hi += 1
    levels = profile["level"].to_numpy()
    return {"from": float(levels[lo]), "to": float(levels[hi]), "width": int(hi - lo + 1),
            "center": float((levels[lo] + levels[hi]) / 2),
            "argmax": float(levels[best]), "levels_total": int(len(levels))}


def design_levels(profile: pd.DataFrame, plateau_call: dict, original: float,
                  count: int) -> list[float]:
    """Where to place the variant grid's levels for this parameter.

    Args:
        profile: Output of `marginal`.
        plateau_call: Output of `plateau`.
        original: The value the strategy was built with.
        count: How many levels the budget allows this parameter.

    Returns:
        Levels spanning symmetrically around the plateau centre, **widened when necessary
        to contain both the original tuple and the in-sample argmax**, and **snapped to
        values the SPP actually explored**.

        The centre of an in-sample plateau is an estimate, not a fact. Centre on it and
        trim, and an out-of-sample plateau that moved falls outside the grid entirely and
        nobody finds out. The span is clipped to the levels the SPP explored, because
        extrapolating past them asserts something the data never measured.

        Snapping is not cosmetic. These parameters are bar counts and periods: a linear
        span produces a shift of 0.1429 bars and an exit after 10.3333 bars, which SQX
        cannot run. Snapping to the observed levels keeps every value legal and carries
        the parameter's real granularity without having to guess its type. Fewer levels
        than `count` come back when the range does not hold that many, which is the
        honest answer rather than inventing intermediate values.
    """
    centre = plateau_call["center"]
    must = [original, plateau_call["argmax"], plateau_call["from"], plateau_call["to"]]
    reach = max(abs(centre - m) for m in must)
    levels = profile["level"].to_numpy()
    lo, hi = max(centre - reach, levels.min()), min(centre + reach, levels.max())
    inside = levels[(levels >= lo) & (levels <= hi)]
    wanted = np.linspace(lo, hi, count)
    snapped = inside[np.abs(inside[None, :] - wanted[:, None]).argmin(axis=1)]
    return sorted({round(float(v), 6) for v in snapped})
