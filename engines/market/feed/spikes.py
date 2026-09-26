"""Spikes on the close and on the wick, in units of the bar's own scale, and whether they reverted."""

import numpy as np


def wick_excursion(o: np.ndarray, h: np.ndarray, low: np.ndarray, c: np.ndarray
                   ) -> tuple[np.ndarray, np.ndarray]:
    """How far each bar's wick reaches past its body, on the side that reaches further.

    Args:
        o, h, low, c: Prices per bar.

    Returns:
        (the excess as a log ratio, the price the wick reached). The body is what the close
        sees; the excess past it is what touches a stop without moving the close.
    """
    up = np.log(h / np.maximum(o, c))
    down = np.log(np.minimum(o, c) / low)
    return np.maximum(up, down), np.where(up >= down, h, low)


def reverted(c: np.ndarray, at: np.ndarray, i: np.ndarray, reach: np.ndarray, m: int,
             rho: float) -> np.ndarray:
    """Whether the price came back to within (1 - rho) of a jump, m bars later.

    Args:
        c: Close per bar.
        at: Bar times in whole minutes.
        i: Indices of the spike bars; each needs the bar before it one minute earlier.
        reach: The jump each spike made from the previous close, as a log ratio's size.
        m: Bars to wait.
        rho: Share of the jump that must be undone.

    Returns:
        One bool per spike: |ln(C[i+m] / C[i-1])| <= (1 - rho) · reach. A spike whose m
        following minutes are not all there cannot show a return and reads False.
    """
    j = np.minimum(i + m, len(c) - 1)
    whole = (i + m < len(c)) & (at[j] - at[i] == m)
    back = np.abs(np.log(c[j] / c[i - 1]))
    # A return of exactly rho is a return: the tolerance only absorbs float rounding.
    return whole & (back <= (1 - rho) * reach * (1 + 1e-9))


def spikes(o: np.ndarray, h: np.ndarray, low: np.ndarray, c: np.ndarray, at: np.ndarray,
           r: np.ndarray, sigma: np.ndarray) -> dict:
    """Each bar's move on the close and on the wick, in multiples of its scale.

    Args:
        o, h, low, c: Prices per bar.
        at: Bar times in whole minutes.
        r: Close-to-close log returns, NaN across a hole.
        sigma: Each bar's scale (engines.market.feed.scale.sigma).

    Returns:
        {"z_close", "z_wick", "wick_price"} per bar. z is 0 where it cannot be measured —
        no scale yet, or no previous minute for the close — so a threshold never fires there.
    """
    exc, price = wick_excursion(o, h, low, c)
    z_close = np.nan_to_num(np.abs(r) / sigma)
    z_wick = np.nan_to_num(exc / sigma)
    return {"z_close": z_close, "z_wick": z_wick, "wick_price": price}


def classify(c: np.ndarray, at: np.ndarray, z: np.ndarray, reach: np.ndarray, k: float,
             m: int, rho: float) -> tuple[np.ndarray, np.ndarray]:
    """The bars over K on one column, and which of them reverted.

    Args:
        c: Close per bar.
        at: Bar times in whole minutes.
        z: One column of spikes() (close or wick).
        reach: The same column's jump from the previous close, as a log ratio's size.
        k: Threshold, in multiples of the scale.
        m, rho: As in reverted().

    Returns:
        (indices of the bars at or over K, a bool per index: spike-and-revert). A bar whose
        previous minute is missing has no reference close and never reverts.
    """
    i = np.flatnonzero(z >= k)
    i = i[i > 0]
    back = reverted(c, at, i, reach[i], m, rho) & (at[i] - at[i - 1] == 1)
    return i, back
