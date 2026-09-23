"""How many independent things were really tried here, and what that does to the best Sharpe."""

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

from core import significance
from core.surface import plateau
from strategies.walkForwardCorrelation import cscv

FLOOR = 2            # fewest clusters worth testing


def distances(window: pd.DataFrame) -> np.ndarray:
    """How far apart two variants are, measured by how differently they earn.

    Args:
        window: The in-sample panel, periods down and variants across.

    Returns:
        A square matrix of sqrt((1 - rho) / 2): zero for variants that move together,
        one for variants that move oppositely. Correlation of returns is the right
        distance here because two parameter sets that produce the same P&L week after
        week are one trial wearing two names, whatever their parameters say.
    """
    corr = np.corrcoef(window.to_numpy().T)
    return np.sqrt(np.clip((1 - np.nan_to_num(corr, nan=0.0)) / 2, 0, None))


def silhouette(dist: np.ndarray, labels: np.ndarray) -> float:
    """How well a labelling separates the variants, averaged over all of them.

    Args:
        dist: What `distances` returned.
        labels: One cluster number per variant.

    Returns:
        The mean silhouette, between -1 and 1. Each variant is scored on how much closer
        it sits to its own cluster than to the nearest other one, so the count that
        maximises it is the count the correlations themselves support rather than one
        picked to make a number come out.

        ⚠️ **A variant alone in its cluster scores zero, by convention and for a reason.**
        Scoring it on how far it sits from everything else would make it perfect, and the
        count that wins would then be two: one outlier, and the other 478. Measured here
        on 2026-09-22 -- it was the difference between reporting 2 independent trials and
        reporting 21.
    """
    members = pd.get_dummies(labels).to_numpy().astype(float)
    counts = members.sum(axis=0)
    totals = dist @ members
    own = np.argmax(members, axis=1)
    alone = counts[own] == 1
    inside = totals[np.arange(len(labels)), own] / np.maximum(counts[own] - 1, 1)
    outside = np.where(members.astype(bool), np.inf, totals / counts).min(axis=1)
    scored = (outside - inside) / np.maximum(inside, outside)
    return float(np.where(alone, 0.0, scored).mean())


def independent(window: pd.DataFrame, k_max: int) -> dict:
    """The number of genuinely distinct trials behind this surface.

    Args:
        window: The in-sample panel.
        k_max: Largest cluster count to consider.

    Returns:
        The chosen count, its silhouette, and the count of variants.

        Five thousand variants of one mother are not five thousand trials: they share a
        rule tree and most of their trades. Deflating a Sharpe by the raw count would
        set a bar nothing could clear and call a real edge luck.

        ⚠️ **A split where one cluster holds half the variants is not considered**, and
        that rule is doing real work. Left to itself the silhouette prefers putting every
        variant in one cluster and a single outlier in another -- measured here, 478
        against 1, scoring 0.51 where the balanced split scored 0.34. It is not a bug in
        the score: with a median correlation of 0.80 between variants, this really is one
        blob with an outlier. But it is the answer that deflates the Sharpe least, and a
        study built to resist overfitting does not get to pick the most flattering count.
    """
    dist = distances(window)
    tree = linkage(squareform(dist, checks=False), method="average")
    scored = {}
    for k in range(FLOOR, min(k_max, window.shape[1] - 1) + 1):
        labels = fcluster(tree, k, criterion="maxclust")
        if np.bincount(labels).max() * 2 <= len(labels):
            scored[k] = silhouette(dist, labels)
    best = max(scored, key=scored.get)
    return {"n_clusters": best, "silhouette": round(scored[best], 4),
            "n_variants": int(window.shape[1])}


def deflated(window: pd.DataFrame, pick: int, n_eff: int) -> dict:
    """Is the best variant's Sharpe real, given how many were tried to find it?

    Args:
        window: The in-sample panel.
        pick: Position of the variant being judged.
        n_eff: Independent trials, from `independent`.

    Returns:
        What `core.surface.plateau.deflated_sharpe` returns. **Every Sharpe here is per
        period**, the unit that function's docstring insists on: the returns, the spread
        across trials and the benchmark are all computed off the same weekly panel, so
        nothing is annualised on one side of the comparison and not the other.
    """
    returns = window.to_numpy()[:, pick]
    observed, skew, kurtosis = significance.moments(returns)
    spread = float(cscv.sharpe(window.to_numpy()).std(ddof=1))
    return plateau.deflated_sharpe(observed, spread, n_eff, len(returns), skew, kurtosis)
