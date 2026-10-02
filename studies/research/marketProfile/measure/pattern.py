"""Bar states, written for longs: does the state shift the odds of the next bar closing up."""

import numpy as np

from studies.research.marketProfile.measure.trades import after, hit


def _state(x: dict, cal: dict, mask: np.ndarray) -> tuple:
    """A bar state as (shift of the up-probability over one bar, entry, exit, detail)."""
    entry, leave = after(mask, 1)
    return hit(x, entry, leave, cal["least"]), entry, leave, {}


def inside(x: dict, cal: dict) -> tuple:
    """An inside bar that closes up."""
    o, h, l, c = x["o"], x["h"], x["l"], x["c"]
    mask = np.zeros(c.size, dtype=bool)
    mask[1:] = (h[1:] < h[:-1]) & (l[1:] > l[:-1]) & (c[1:] > o[1:])
    return _state(x, cal, mask)


def engulfing(x: dict, cal: dict) -> tuple:
    """An up bar whose body engulfs the body of the down bar before it."""
    o, c = x["o"], x["c"]
    mask = np.zeros(c.size, dtype=bool)
    mask[1:] = (c[:-1] < o[:-1]) & (c[1:] > o[1:]) & (c[1:] >= o[:-1]) & (o[1:] <= c[:-1])
    return _state(x, cal, mask)


def run(x: dict, cal: dict, k: int, follow: bool) -> tuple:
    """k closes in a row: up closes bought (follow) or down closes bought (fade)."""
    step = np.diff(x["c"], prepend=x["c"][0])
    one = step > 0 if follow else step < 0
    mask = one.copy()
    for j in range(1, k):
        mask[j:] &= one[:-j]
    return _state(x, cal, mask)
