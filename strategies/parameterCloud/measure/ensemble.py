"""C1: what a spread of plateau members earns together, against the single chosen point."""

import numpy as np
import pandas as pd

ANNUAL = 252


def members(frame: pd.DataFrame, values: np.ndarray, mask: np.ndarray,
            origin_row: int, delta: float) -> pd.Index:
    """The plateau: the neighbours that perform within a shortfall of the origin.

    Args:
        frame: The metric panel.
        values: The metric, one per row.
        mask: The neighbourhood mask from `neighbourhood.near`.
        origin_row: Row index of theta-zero.
        delta: Relative shortfall still counted as plateau.

    Returns:
        Variant ids, the origin included. Membership is by performance **and** by
        proximity: a distant tuple that scores well is a different strategy, not a
        neighbour to share risk with.
    """
    reference = values[origin_row]
    near = mask & (values >= reference - delta * abs(reference))
    return pd.Index(frame.loc[near, "variant_id"])


def spread(coords: pd.DataFrame, pool: pd.Index, k: int) -> pd.Index:
    """K plateau members spread across the plateau rather than the K best.

    Args:
        coords: Parameters on [0, 1], indexed by variant id.
        pool: What `members` returned.
        k: How many to pick.

    Returns:
        Variant ids, the first being the pool's own centroid-nearest member. Greedy
        farthest-point: each pick is the member furthest from everything picked so far.
        Picking the K best instead would be selection wearing an ensemble's clothes --
        the whole point is to stop depending on which point scored highest.
    """
    seats = coords.loc[coords.index.intersection(pool)]
    chosen = [int(np.argmin(np.linalg.norm(seats - seats.mean(), axis=1)))]
    while len(chosen) < min(k, len(seats)):
        far = np.linalg.norm(seats.to_numpy()[:, None] - seats.to_numpy()[chosen], axis=2)
        chosen.append(int(np.argmax(far.min(axis=1))))
    return seats.index[chosen]


def statistics(daily: pd.Series) -> dict:
    """What one equity stream is worth.

    Args:
        daily: P&L per day.

    Returns:
        Net, annualised Sharpe and maximum drawdown, all in account currency except the
        Sharpe. The drawdown is taken on the cumulative curve, so it is a real peak to
        trough and not a per-day statistic.
    """
    curve = daily.cumsum()
    return {"net": float(daily.sum()),
            "sharpe": float(daily.mean() / daily.std() * np.sqrt(ANNUAL)),
            "drawdown": float((curve - curve.cummax()).min())}


def blend(daily: pd.DataFrame, picked: pd.Index, origin: str) -> dict:
    """The equal-weight ensemble against the single point, on the same days.

    Args:
        daily: Days down, variant across, P&L per day.
        picked: What `spread` returned.
        origin: The origin's variant id.

    Returns:
        `single`, `blended`, the `gap` in Sharpe, and which members carried it. Each
        member is taken at 1/K of the risk, so the blend is a reallocation and not extra
        capital.

        **Diagnostic, never a substitute.** If the single point beats the blend by a wide
        margin, most of that margin is the part of its score that its neighbours did not
        reproduce, which is overfit. It is not an argument for keeping the single point.
    """
    seats = [c for c in picked if c in daily.columns]
    single, blended = statistics(daily[origin]), statistics(daily[seats].mean(axis=1))
    return {"k": len(seats), "picked": seats, "single": single, "blended": blended,
            "gap": single["sharpe"] - blended["sharpe"]}
