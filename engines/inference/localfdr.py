"""Local false discovery rate of one lot of z, against the lot's own empirical null."""

from typing import TypedDict

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import minimize
from scipy.stats import norm

MIN_Z = 500  # a null and a density fitted on fewer z are noise: p is left empty
BINS, SMOOTH = (
    60,
    1.5,
)  # the density: a histogram of 60 bins, Gaussian-smoothed over 1.5 bins


def _nll(t: np.ndarray, inside: np.ndarray, lo: float, hi: float) -> float:
    """Negative log-likelihood of N(t[0], t[1]^2) truncated to [lo, hi]."""
    mass = norm.cdf(hi, t[0], abs(t[1])) - norm.cdf(lo, t[0], abs(t[1]))
    return -(norm.logpdf(inside, t[0], abs(t[1])) - np.log(mass)).sum()


def empirical_null(z: np.ndarray) -> tuple[float, float, float]:
    """The null N(delta0, sigma0^2) and pi0, from the central 50 % of z (Efron's empirical null).

    Args:
        z: One lot's z, finite.

    Returns:
        (delta0, sigma0, pi0): the maximum-likelihood normal truncated to the 25-75 % range of
        z, and the lot's share inside that range over the share the normal puts there, capped
        at 1.
    """
    lo, hi = np.quantile(z, [0.25, 0.75])
    inside = z[(z >= lo) & (z <= hi)]

    d, s = minimize(
        _nll, [inside.mean(), inside.std()], args=(inside, lo, hi), method="Nelder-Mead"
    ).x
    s = abs(s)
    return (
        float(d),
        float(s),
        float(
            min(1.0, len(inside) / len(z) / (norm.cdf(hi, d, s) - norm.cdf(lo, d, s)))
        ),
    )


class Fit(TypedDict):
    """fit() — posterior non-null probability and the empirical null."""

    p: np.ndarray | None
    delta0: float | None
    sigma0: float | None
    pi0: float | None
    reason: str


def fit(z: np.ndarray) -> Fit:
    """p_i = 1 - fdr(z_i): the posterior probability that strategy i is not null.

    Args:
        z: One lot's z, finite, one per strategy.

    Returns:
        {"p", "delta0", "sigma0", "pi0", "reason"}. fdr = pi0 f0(z) / f(z), f0 the empirical
        null, f the smoothed histogram of the lot; clipped to [0, 1] and made non-increasing in
        z by the cumulative maximum from the right: a z is as null as the worst fdr at or above it,
        so the lot's peaked centre cannot lend its low fdr to a tail lighter than the null (that
        tail gets p = 0, nobody stands out). One-sided: p = 0 for z <= delta0, since only the
        right tail can be an edge. `p` is an array like `z`; with fewer than MIN_Z z it is None,
        the three figures are None and `reason` says why.
    """
    if len(z) < MIN_Z:
        return {
            "p": None,
            "delta0": None,
            "sigma0": None,
            "pi0": None,
            "reason": f"{len(z)} z, menos de {MIN_Z}: el ajuste sería ruido",
        }
    d, s, pi0 = empirical_null(z)
    counts, edges = np.histogram(z, BINS)
    width = edges[1] - edges[0]
    f = gaussian_filter1d(counts.astype(float), SMOOTH) / (len(z) * width)
    f = np.interp(z, (edges[1:] + edges[:-1]) / 2, np.maximum(f, 1e-12))
    fdr = np.clip(pi0 * norm.pdf(z, d, s) / f, 0, 1)
    order = np.argsort(z)
    fdr[order] = np.maximum.accumulate(fdr[order][::-1])[::-1]
    return {
        "p": np.where(z > d, 1 - fdr, 0.0),
        "delta0": d,
        "sigma0": s,
        "pi0": pi0,
        "reason": "",
    }
