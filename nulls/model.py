"""What could have happened instead: the ladder of nulls, and what each rung hands to chance.

Whatever a rung holds fixed, it gives to the null -- so a rung does not measure edge, it
attributes it. Match everything and the null is the strategy itself, p is 0.5 and nothing was
measured; match nothing and the null is a monkey with the same opportunity set. The difference
between two consecutive rungs is what that one channel was worth. Every rung shares the
signature `(located, draws, rng)` in and entries, holds and sizes out."""

import numpy as np

# Random placement can overlap, where the real trades never do. At the occupancy this corpus
# runs at -- 7.4% of bars held, measured 2026-09-22 -- that is rare, and dropping the
# overlaps would change n and make the statistic incomparable to the real run. It is a
# declared simplification, not an oversight.


def _place(located: dict, holds: np.ndarray, draws: int, rng: np.random.Generator) -> np.ndarray:
    """Uniform entry bars, each late enough that its own hold still fits the window.

    Args:
        located: What inputs.on_grid() returned.
        holds: Bars each drawn trade is held, shape (draws, trades).
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Entry bar index, shape (draws, trades). The upper bound is per trade rather than a
        single one taken from the longest hold, which would leave the end of the window
        unreachable for every short trade and quietly bias the null away from it.
    """
    lo, hi = located["window"]
    return (lo + rng.random((draws, holds.shape[1])) * (hi - holds - lo)).astype(np.int64)


def timing(located: dict, draws: int, rng: np.random.Generator) -> dict:
    """Move every trade, keeping its own holding time and its own size.

    Args:
        located: What inputs.on_grid() returned.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Keys `entries`, `holds`, `sizes`, each shape (draws, trades).
    """
    holds = np.tile(located["hold"], (draws, 1))
    return {"entries": _place(located, holds, draws, rng), "holds": holds,
            "sizes": np.tile(located["size"], (draws, 1))}


def timing_holds(located: dict, draws: int, rng: np.random.Generator) -> dict:
    """Move every trade and redraw how long it is held, keeping its size.

    Args:
        located: What inputs.on_grid() returned.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Keys `entries`, `holds`, `sizes`. Holds are resampled with replacement from the
        strategy's own holding times, so the distribution survives and the pairing with a
        particular trade does not -- which is what breaks the leak from a path-dependent
        exit, whose realised duration is short precisely because it worked.
    """
    pool = located["hold"]
    holds = rng.choice(pool, size=(draws, len(pool)), replace=True)
    return {"entries": _place(located, holds, draws, rng), "holds": holds,
            "sizes": np.tile(located["size"], (draws, 1))}


def timing_sizing(located: dict, draws: int, rng: np.random.Generator) -> dict:
    """Move every trade and strip the volatility normalisation from its size.

    Args:
        located: What inputs.on_grid() returned.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Keys `entries`, `holds`, `sizes`. Every trade is sized the same, at the strategy's
        own mean, so the null risks the same money in total and allocates it without regard
        to volatility. Against `timing`, the gap is what sizing by ATR was worth -- and it
        is worth it through the variance, not the mean, which is why no correlation between
        size and per-unit return can find it.
    """
    holds = np.tile(located["hold"], (draws, 1))
    flat = np.full_like(holds, located["size"].mean(), dtype=np.float64)
    return {"entries": _place(located, holds, draws, rng), "holds": holds, "sizes": flat}


def free(located: dict, draws: int, rng: np.random.Generator) -> dict:
    """Move every trade, redraw its holding time and strip its sizing.

    Args:
        located: What inputs.on_grid() returned.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Keys `entries`, `holds`, `sizes`. The bottom of the ladder: only the trade count and
        the cost survive, so this is the monkey, and its p is the one that speaks about
        total edge rather than about one channel.
    """
    drawn = timing_holds(located, draws, rng)
    drawn["sizes"] = np.full_like(drawn["holds"], located["size"].mean(), dtype=np.float64)
    return drawn


RUNGS = {"timing": timing, "timing_holds": timing_holds,
         "timing_sizing": timing_sizing, "free": free}

# What each rung hands to chance. A rung that randomises more than one thing cannot attribute
# a low p to any single cause, which is why the summary reports `timing` and the others are
# read beside it -- and why the attribution is the gap between two rungs, never one rung alone.
RANDOMISES = {"timing": "when each trade is entered",
              "timing_holds": "when each trade is entered, and how long it is held",
              "timing_sizing": "when each trade is entered, and the sizing by volatility",
              "free": "when, how long, and how big -- only the trade count and the cost remain"}
