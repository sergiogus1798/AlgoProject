"""What could have happened instead: the ladder of nulls, and what each rung hands to chance.

Whatever a rung holds fixed, it gives to the null -- so a rung does not measure edge, it
attributes it. Match everything and the null is the strategy itself, p is 0.5 and nothing was
measured; match nothing and the null is a monkey with the same opportunity set. The difference
between two consecutive rungs is what that one channel was worth. Every rung shares the
signature `(located, draws, rng)` in and entries, holds and sizes out -- or, asked
`placed=False`, the uniforms that place the entries, for the kernel that places as it prices."""

import numpy as np

from engines.market.calibrate import OnGrid

# Random placement can overlap, where the real trades never do. At the occupancy this corpus
# runs at -- 7.4% of bars held, measured 2026-09-22 -- that is rare, and dropping the
# overlaps would change n and make the statistic incomparable to the real run. It is a
# declared simplification, not an oversight.


def _place(located: OnGrid, holds: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Uniform entry bars, each late enough that its own hold still fits the window.

    Args:
        located: What inputs.on_grid() returned.
        holds: Bars each drawn trade is held, shape (draws, trades).
        u: One uniform per drawn trade, same shape.

    Returns:
        Entry bar index, shape (draws, trades). The upper bound is per trade rather than a
        single one taken from the longest hold, which would leave the end of the window
        unreachable for every short trade and quietly bias the null away from it.
        `kernel.ladder` computes this same expression trade by trade: change both or neither.
    """
    lo, hi = located["window"]
    return (lo + u * (hi - holds - lo + 1)).astype(np.int64)


def _rung(
    located: OnGrid,
    draws: int,
    rng: np.random.Generator,
    placed: bool,
    redraw: bool,
    flat: bool,
) -> dict[str, np.ndarray]:
    """The draw every rung is, differing only in what it hands to chance beyond the entry.

    Args:
        located: What inputs.on_grid() returned.
        draws: How many runs.
        rng: Seeded generator; one per block, the SAME for the four rungs (see below).
        placed: False to hand back the uniforms `u` instead of the `entries` they place --
            what `kernel.ladder` takes, sparing the int64 matrix.
        redraw: Resample the holds with replacement from the strategy's own holding times,
            so the distribution survives and the pairing with a trade does not -- which breaks
            the leak from a path-dependent exit, whose duration is short because it worked.
        flat: Size every trade at the strategy's mean, so the null risks the same money and
            spreads it without regard to volatility.

    Returns:
        Keys `holds`, `sizes`, and `entries` or `u`, each (draws, trades). Since 2026-10-13 the
        four rungs read ONE stream (encargo 66, N12 B; common random numbers): the uniforms
        `u` come first and are the same for every rung, the redrawn holds come second and are
        the same for the two rungs that redraw them. A rung maps `u` onto the bars its hold
        leaves room for, so the entries of `timing` and `timing_sizing` are identical, as are
        those of `timing_holds` and `free`; a rung alone is the null it always was.
    """
    n = located["hold"].size
    u = rng.random((draws, n))
    holds = (
        rng.choice(located["hold"], size=(draws, n), replace=True)
        if redraw
        else np.broadcast_to(located["hold"], (draws, n))
    )
    sizes = np.broadcast_to(
        located["size"].mean() if flat else located["size"], holds.shape
    )
    if placed:
        return {"entries": _place(located, holds, u), "holds": holds, "sizes": sizes}
    return {"u": u, "holds": holds, "sizes": sizes}


def timing(
    located: OnGrid, draws: int, rng: np.random.Generator, placed: bool = True
) -> dict[str, np.ndarray]:
    """Move every trade, keeping its own holding time and its own size (see `_rung`)."""
    return _rung(located, draws, rng, placed, False, False)


def timing_holds(
    located: OnGrid, draws: int, rng: np.random.Generator, placed: bool = True
) -> dict[str, np.ndarray]:
    """Move every trade and redraw how long it is held, keeping its size (see `_rung`)."""
    return _rung(located, draws, rng, placed, True, False)


def timing_sizing(
    located: OnGrid, draws: int, rng: np.random.Generator, placed: bool = True
) -> dict[str, np.ndarray]:
    """Move every trade and strip the volatility normalisation from its size (see `_rung`).

    Against `timing`, the gap is what sizing by ATR was worth -- through the variance, not the
    mean, which is why no correlation between size and per-unit return can find it.
    """
    return _rung(located, draws, rng, placed, False, True)


def free(
    located: OnGrid, draws: int, rng: np.random.Generator, placed: bool = True
) -> dict[str, np.ndarray]:
    """Move every trade, redraw its holding time and strip its sizing (see `_rung`).

    The bottom of the ladder: only the trade count and the cost survive, so this is the
    monkey, and its p is the one that speaks about total edge rather than about one channel.
    """
    return _rung(located, draws, rng, placed, True, True)


RUNGS = {
    "timing": timing,
    "timing_holds": timing_holds,
    "timing_sizing": timing_sizing,
    "free": free,
}

# What each rung hands to chance. A rung that randomises more than one thing cannot attribute
# a low p to any single cause, which is why the summary reports `timing` and the others are
# read beside it -- and why the attribution is the gap between two rungs, never one rung alone.
RANDOMISES = {
    "timing": "when each trade is entered",
    "timing_holds": "when each trade is entered, and how long it is held",
    "timing_sizing": "when each trade is entered, and the sizing by volatility",
    "free": "when, how long, and how big -- only the trade count and the cost remain",
}
