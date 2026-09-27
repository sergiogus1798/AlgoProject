"""The daily spread as a curve of price: its mean and its quantile band, for the MC Retest's spread range.

The owner's shape, 2026-09-27: the simplest curve, a power law `spread = a · price^b`, fitted
in log-log. The mean by least squares brought back with the smearing factor; each quantile by
quantile regression (the check loss solved as a linear programme), so the band may widen or
narrow with price on its own slope instead of being the mean's shifted by a constant.
"""

import numpy as np
import pandas as pd
from scipy.optimize import linprog


def days(m: pd.DataFrame, tick: float, min_minutes: int) -> pd.DataFrame:
    """One row per day with enough quoted minutes: mean spread in points and median bid.

    Args:
        m: `inputs.minutes()`.
        tick: `assets/`'s tick size, the unit SQX's spread is in.
        min_minutes: Holidays and half days below this are dropped.
    """
    day = m.index.normalize()
    got = pd.DataFrame({"spread": m["spread_open"].groupby(day).mean() / tick,
                        "price": m["bid_open"].groupby(day).median(),
                        "minutes": m["n"].groupby(day).size()})
    return got[(got["minutes"] >= min_minutes) & (got["spread"] > 0)]


def _quantile(x: np.ndarray, y: np.ndarray, q: float) -> np.ndarray:
    """Intercept and slope minimising the check loss of quantile q (linear programme)."""
    n = len(y)
    design = np.column_stack([np.ones(n), x])
    cost = np.concatenate([np.zeros(2), np.full(n, q), np.full(n, 1 - q)])
    equal = np.hstack([design, np.eye(n), -np.eye(n)])
    bounds = [(None, None)] * 2 + [(0, None)] * (2 * n)
    return linprog(cost, A_eq=equal, b_eq=y, bounds=bounds, method="highs").x[:2]


def fit(d: pd.DataFrame, quantiles: list[float]) -> dict:
    """The mean curve and one curve per quantile, all in log-log.

    Returns:
        {"media": {"a", "b", "smear"}, "<q>": {"a", "b"}, ...}: spread = a · price^b.
    """
    x, y = np.log(d["price"].to_numpy()), np.log(d["spread"].to_numpy())
    b, a = np.polyfit(x, y, 1)
    out = {"media": {"a": float(np.exp(a)), "b": float(b),
                     "smear": float(np.exp(np.var(y - (a + b * x)) / 2))}}
    for q in quantiles:
        a_q, b_q = _quantile(x, y, q)
        out[str(q)] = {"a": float(np.exp(a_q)), "b": float(b_q)}
    return out


def predict(curves: dict, price: np.ndarray) -> pd.DataFrame:
    """Every curve at the given prices, in points; one column per curve.

    Quantile curves fitted one by one can cross where the data thin out; at each price they
    are sorted back into order (rearrangement), so the 2.5 % never sits above the median.
    """
    price = np.asarray(price, float)
    got = pd.DataFrame({k: c["a"] * price ** c["b"] * c.get("smear", 1.0) for k, c in curves.items()},
                       index=pd.Index(price, name="precio"))
    qs = [k for k in got.columns if k != "media"]
    got[qs] = np.sort(got[qs].to_numpy(), axis=1)
    return got


def coverage(d: pd.DataFrame, curves: dict, low: str, high: str) -> pd.DataFrame:
    """Per year, the share of days below the low curve and above the high one: the band's calibration."""
    band = predict(curves, d["price"].to_numpy())
    below = pd.Series(d["spread"].to_numpy() < band[low].to_numpy(), d.index)
    above = pd.Series(d["spread"].to_numpy() > band[high].to_numpy(), d.index)
    year = d.index.year
    return pd.DataFrame({"días": below.groupby(year).size(),
                         "% por debajo": below.groupby(year).mean() * 100,
                         "% por encima": above.groupby(year).mean() * 100})
