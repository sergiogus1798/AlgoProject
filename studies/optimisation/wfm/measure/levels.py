"""L1 and L2 on the weekly oos2 panel against the shared-sign flip null, and the cells' redundancy."""

import numpy as np
import pandas as pd
from scipy.stats import skew

from engines.weekly import flip


def l1(cells: pd.DataFrame, signs: np.ndarray, years: float) -> dict:
    """The median cell's excess per year in oos2, and where it falls in the null.

    Args:
        cells: Weeks x cells of net excess (`excess.weekly`).
        signs: `flip.signs`: draws x weeks of +-1, each row applied to every cell alike.
        years: Length of oos2.

    Returns:
        `mediana_exceso` (median over the cells of each one's sum / years), `flip.tails` of
        it among the same median on every draw, and `null`, the draws themselves. A median
        and not a count: the cells are near copies of each other.
    """
    panel = cells.to_numpy()
    observed = float(np.median(panel.sum(axis=0)) / years)
    null = np.median(signs @ panel, axis=1) / years
    return {"mediana_exceso": observed, **flip.tails(observed, null), "null": null}


def reference(cells: pd.DataFrame, mode: str, centre: str) -> pd.Series:
    """The re-optimised strategy as one weekly series, by how it would be traded.

    Args:
        cells: Weeks x cells of net excess.
        mode: `fijo` or `reoptimizado`.
        centre: The traded cell's name.

    Returns:
        `fijo`: the median across cells of each WEEK (a series; its sum is not the median of
        the cells' sums that L1 reads). `reoptimizado`: the centre cell's column.
    """
    return cells[centre] if mode == "reoptimizado" else cells.median(axis=1)


def l2(ref: pd.Series, mother: pd.Series, signs: np.ndarray, years: float) -> dict:
    """Re-optimising against freezing: the weekly difference, under the same sign sets.

    Args:
        ref: reference()'s series.
        mother: The mother with fixed parameters, same weeks, re-charged the same way.
        signs: The very matrix l1() took.
        years: Length of oos2.

    Returns:
        `delta` (sum of ref - mother per year), `flip.tails` of it, and `null`.
    """
    diff = (ref - mother).to_numpy()
    observed = float(diff.sum() / years)
    null = signs @ diff / years
    return {"delta": observed, **flip.tails(observed, null), "null": null}


def effective(cells: pd.DataFrame) -> float:
    """How many independent curves the cells are worth: (sum of eigenvalues)^2 / sum of squares.

    Args:
        cells: Weeks x cells of net excess; a cell that never moved is left out.

    Returns:
        1 for identical curves, the number of cells for uncorrelated ones. On W weeks even
        truly independent cells read about N / (1 + (N - 1) / W): 25 of 30 on 143 weeks.
    """
    live = cells.loc[:, cells.std() > 0]
    values = np.linalg.eigvalsh(np.corrcoef(live.to_numpy(), rowvar=False))
    return float(values.sum() ** 2 / (values ** 2).sum())


def skewness(cells: pd.DataFrame) -> float:
    """Skewness of the weekly median-of-cells series: what the null's symmetry assumes is zero."""
    return float(skew(cells.median(axis=1).to_numpy()))
