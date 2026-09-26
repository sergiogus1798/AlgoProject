"""Between two markets' surfaces: the rank correlation and the overlap of their top shares."""

import math

import numpy as np
import pandas as pd
from scipy.stats import hypergeom

from core.surface import dedupe

Z95 = 1.959964


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson's r on average ranks, which is Spearman's rho.

    Args:
        a, b: One value per variant, same order.

    Returns:
        The coefficient; NaN when either side is constant.
    """
    ra, rb = pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def neutral(a: np.ndarray, b: np.ndarray, ca: np.ndarray, cb: np.ndarray) -> float:
    """Spearman of two surfaces once each has lost what its own covariate explains.

    Args:
        a, b: One value per variant, same order.
        ca, cb: The covariate of each side, e.g. each market's exposure.

    Returns:
        Pearson's r of the rank residuals, each surface's ranks regressed on its own
        covariate's ranks. 🔬 2026-09-26: on long-only strategies net profit is partly
        time-in-market times the market's drift, so two markets that drifted apart rank
        the variants AGAINST each other by exposure alone — 23-1-46 oos1, USDJPY against
        AUDUSD, reads -0.70 raw and -0.39 without it. This is the reading that is left.
    """
    def residual(y: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Ranks of y minus their linear fit on the ranks of x."""
        ry, rx = pd.Series(y).rank().to_numpy(), pd.Series(x).rank().to_numpy()
        if rx.std() == 0:
            return ry - ry.mean()
        return ry - np.polyval(np.polyfit(rx, ry, 1), rx)

    ea, eb = residual(a, ca), residual(b, cb)
    if ea.std() == 0 or eb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ea, eb)[0, 1])


def top(values: pd.Series, share: float) -> set:
    """The labels of the best `share` of a surface.

    Args:
        values: One value per variant, indexed by `variant_id`.
        share: 0.10 for the top decile.

    Returns:
        ceil(share * n) labels. Ties at the cut are broken by label, so the set is the
        same on every run and the overlap is never a matter of sort order.
    """
    k = max(1, math.ceil(share * len(values)))
    order = values.rename("v").reset_index().sort_values(["v", values.index.name or "index"],
                                                         ascending=[False, True])
    return set(order.iloc[:k, 0])


def chance(n: int, k: int, quantile: float) -> tuple[float, float]:
    """What the Jaccard of two top-k sets reads when the two rankings are independent.

    Args:
        n: Variants both surfaces share.
        k: Size of each top set.
        quantile: The upper quantile of the band, e.g. 0.975.

    Returns:
        (expected J, J at that quantile). The overlap of two independent k-subsets of n is
        hypergeometric with mean k^2/n, and J = x / (2k - x). At the top decile of any n
        the expectation is about 0.053, not zero: two random deciles always share a tenth.
    """
    mean = k * k / n
    hi = float(hypergeom.ppf(quantile, n, k, k))
    return mean / (2 * k - mean), hi / (2 * k - hi)


def pair(a: pd.Series, b: pd.Series, share: float, quantile: float,
         ca: pd.Series, cb: pd.Series) -> dict:
    """rho_ab and J_ab over the variants both markets keep, each distinct backtest once.

    Args:
        a, b: One market's surface each, indexed by `variant_id`, NaN where unusable.
        share: The top share J is taken on.
        quantile: The band's upper quantile under independence.
        ca, cb: Each market's exposure per variant, for `rho_neutral`.

    Returns:
        n (rows both keep), n_eff (distinct result pairs), rho and its Fisher interval on
        n_eff, `rho_neutral` (see `neutral`), J, its expectation and band under
        independence, and the hypergeometric p of the overlap. Inert parameters duplicate a backtest under several tuples, and
        counting it several times narrows every interval for nothing (`core.surface`).
        ⚠️ Distinct is not independent: the design clusters tuples, so both the interval
        and the band are still narrower than the truth.
    """
    both = pd.DataFrame({"a": a, "b": b, "ca": ca, "cb": cb}).dropna(subset=["a", "b"])
    kept = dedupe.distinct(both, ("a", "b"))
    n = len(kept)
    rho = spearman(kept["a"].to_numpy(), kept["b"].to_numpy())
    z, half = np.arctanh(np.clip(rho, -0.999999, 0.999999)), Z95 / math.sqrt(max(n - 3, 1))
    ta, tb = top(kept["a"], share), top(kept["b"], share)
    k, x = len(ta), len(ta & tb)
    j0, j_hi = chance(n, k, quantile)
    return {"n": len(both), "n_eff": n, "rho": rho,
            "rho_lo": float(np.tanh(z - half)), "rho_hi": float(np.tanh(z + half)),
            "rho_neutral": neutral(*(kept[c].to_numpy() for c in ("a", "b", "ca", "cb"))),
            "k": k, "overlap": x, "j": x / (2 * k - x), "j0": j0, "j_hi": j_hi,
            "p_overlap": float(hypergeom.sf(x - 1, n, k, k))}


def matrix(surfaces: pd.DataFrame, exposure: pd.DataFrame, share: float,
           quantile: float) -> pd.DataFrame:
    """Every pair of one segment's markets, the diagonal included.

    Args:
        surfaces: What `inputs.surfaces.wide` returned.
        exposure: The same shape, each market's exposure.
        share: The top share J is taken on.
        quantile: The band's upper quantile under independence.

    Returns:
        One row per unordered pair (a, b) with a <= b in column order, carrying what `pair`
        returns. The diagonal is kept on purpose: rho of a market with itself must read 1.0,
        and it is the cheapest check that the variants were paired by identity.
    """
    names = list(surfaces.columns)
    return pd.DataFrame([{"a": a, "b": b, **pair(surfaces[a], surfaces[b], share, quantile,
                                                 exposure[a], exposure[b])}
                         for i, a in enumerate(names) for b in names[i:]])
