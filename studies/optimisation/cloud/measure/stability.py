"""B2: whether the shape of the surface survives being cut into periods."""

import numpy as np
import pandas as pd
from scipy import stats

ANNUAL = 252


def periods(daily: pd.DataFrame, freq: str) -> dict:
    """Every variant's result in every period, and how active it was.

    Args:
        daily: Days down, variant across, P&L per day.
        freq: A pandas offset alias -- "YE" for calendar years, "2QE" for half-years.

    Returns:
        `pnl` and `sharpe` -- periods down, variants across -- and `active`, the days on
        which each variant's P&L moved. The Sharpe is annualised from daily P&L, which is
        scale-free and so comparable between a period of 250 days and one of 120.

        **`active` is days, not trades.** A per-period trade count would need the trade
        export, which costs about ninety minutes against this file's 1.5 seconds. It is
        the honest floor available here and the report says so, because a period with
        four active days carries a Sharpe that means nothing.
    """
    group = daily.groupby(pd.Grouper(freq=freq))
    mean, sd = group.mean(), group.std()
    return {"pnl": group.sum(), "active": group.agg(lambda c: int((c != 0).sum())),
            "sharpe": (mean / sd * np.sqrt(ANNUAL)).replace([np.inf, -np.inf], np.nan)}


def usable(per: dict, min_active: int) -> pd.Index:
    """The periods with enough activity behind them to be read.

    Args:
        per: What `periods` returned.
        min_active: Median active days a period needs across the cloud.

    Returns:
        The periods that clear it, in order.
    """
    return per["active"].median(axis=1)[lambda s: s >= min_active].index


def fractions(per: dict, keep: pd.Index) -> pd.Series:
    """f_y: the share of the cloud that made money in each period.

    Args:
        per: What `periods` returned.
        keep: What `usable` returned.

    Returns:
        One probability per period. It separates "the whole family works" from "one lucky
        period carries everything", which no whole-history number can.
    """
    return (per["pnl"].loc[keep] > 0).mean(axis=1)


def persistence(per: dict, keep: pd.Index) -> pd.Series:
    """rho: how much of the ranking between variants survives into the next period.

    Args:
        per: What `periods` returned.
        keep: What `usable` returned.

    Returns:
        Spearman between consecutive periods, indexed by the earlier one, the last period
        dropped. Near zero means the surface is reshuffled every period, and then
        optimising this family in sample is optimising noise -- however good the in-sample
        correlation looked.
    """
    frame = per["sharpe"].loc[keep]
    pairs = [(frame.index[i],
              stats.spearmanr(frame.iloc[i], frame.iloc[i + 1], nan_policy="omit").statistic)
             for i in range(len(frame) - 1)]
    return pd.Series(dict(pairs))


def centroids(per: dict, keep: pd.Index, coords: pd.DataFrame,
              share: float) -> tuple[pd.DataFrame, pd.Series]:
    """c_y and d_y: where the good region sat each period, and how far it moved.

    Args:
        per: What `periods` returned.
        keep: What `usable` returned.
        coords: Parameters on [0, 1], indexed by variant id.
        share: Top fraction of the cloud counted as the good region, 0.1 for the decile.

    Returns:
        The centroid per period, and the distance between consecutive centroids as a
        share of each parameter's own explored range. A large drift means the optimum
        wanders, so re-optimising chases it rather than finding it.
    """
    frame = per["sharpe"].loc[keep]
    rows = {}
    for period, values in frame.iterrows():
        top = values.dropna().nlargest(max(1, int(len(values.dropna()) * share))).index
        rows[period] = coords.loc[coords.index.intersection(top)].mean()
    centre = pd.DataFrame(rows).T
    step = np.linalg.norm(centre.diff().iloc[1:].to_numpy(), axis=1) / np.sqrt(centre.shape[1])
    return centre, pd.Series(step, index=centre.index[:-1])


def origin_rank(per: dict, keep: pd.Index, origin: str) -> pd.Series:
    """Where theta-zero ranked inside the cloud, period by period.

    Args:
        per: What `periods` returned.
        keep: What `usable` returned.
        origin: The origin's variant id.

    Returns:
        A1's rank per period. A point that is first in sample and middling in every
        period afterwards is the picture of a selection, not of an edge.
    """
    frame = per["sharpe"].loc[keep]
    return frame.le(frame[origin], axis=0).mean(axis=1)
