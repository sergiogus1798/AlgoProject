"""The free-placement family: models that lift the whole run and lay it down anywhere in the
backtest window. They destroy the regime a trade landed in, its calendar and its clustering all
at once, so a low p under any of them cannot be attributed to one of the three — which is why
the registry keeps them beside `block_shift` rather than instead of it."""

import numpy as np
import pandas as pd

from strategies.crossmarket.model.holdfit import MIN_HOLD, fit


def _lay(holds: np.ndarray, gaps: np.ndarray, n_bars: int,
         rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Place a sequence of holds and gaps end to end on a circle of bars, from a random start.

    Args:
        holds: A (draws, trades) array of holding times in bars.
        gaps: A (draws, trades) array of flat bars before each trade.
        n_bars: Bars in the circle — the backtest window, or one block of the window sweep.
        rng: Seeded generator.

    Returns:
        Entry indices and holds. Trade k opens gap k bars after trade k-1 closed. A hold is
        zeroed, and its trade drops out of that run the way a Friday-close cut already drops
        one, when it would wrap round onto the first trade of the sequence or run past the
        last bar. That makes non-overlap true by construction. Before 2026-09-15 each trade
        was offset by its *own* hold instead of the previous one's, and 1-7% of the trades of
        every run overlapped another, under all three models, on every pair measured.
    """
    start = rng.integers(0, n_bars, size=(holds.shape[0], 1))
    offset = np.cumsum(gaps, axis=1) + np.cumsum(holds, axis=1) - holds
    entries = (start + offset) % n_bars
    keep = (offset + holds <= n_bars + gaps[:, :1]) & (entries + holds <= n_bars)
    return entries, np.where(keep, holds, 0)


def segment_permute(held: pd.DataFrame, market: dict, draws: int,
                    rng: np.random.Generator, batch: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Reorder the real hold-and-gap segments and lay them from a random start bar.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.
        batch: Runs already produced; unused, this model's randomness is
            sequential. The registry's contract carries it for block_shift.

    Returns:
        Entry indices and holds. Keeps the holds and gaps as multisets but randomises their
        order, so it also destroys the clustering and the calendar — and, unlike block_shift,
        lays the whole run from one random start over the **whole backtest window** rather
        than inside each regime block. A run can therefore land in any part of the window and
        inherit that part's regime, so beating this null is a broader claim than beating
        block_shift's, and a less attributable one because three things changed at once. The
        window is `envelope.window`'s, not the bar file's: before that was enforced this
        model was placing trades in years the real strategy never traded.
    """
    order = np.argsort(rng.random((draws, len(held))), axis=1)
    holds = held["hold"].to_numpy()[order]
    return _lay(holds, market["gaps"][order], market["n_bars"], rng)


def resampled_holds(held: pd.DataFrame, market: dict, draws: int,
                    rng: np.random.Generator, batch: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Draw holds and gaps with replacement from the real ones, and lay them out.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.
        batch: Runs already produced; unused, this model's randomness is
            sequential. The registry's contract carries it for block_shift.

    Returns:
        Entry indices and holds. Unlike segment_permute the multiset is not preserved — a hold
        can appear twice and another not at all — so the run's total time in the market varies
        between draws. That makes it a test of the trading rhythm rather than of this exact
        realisation of it.
    """
    shape = (draws, len(held))
    pick = rng.integers(0, len(held), size=shape)
    return _lay(held["hold"].to_numpy()[pick], market["gaps"][pick], market["n_bars"], rng)


def fitted_holds(held: pd.DataFrame, market: dict, draws: int,
                 rng: np.random.Generator, batch: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Fit a distribution to the real holds and gaps, and draw new ones from it.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.
        batch: Runs already produced; unused, this model's randomness is
            sequential. The registry's contract carries it for block_shift.

    Returns:
        Entry indices and holds. The holds are no longer the real ones, so this model differs
        from the real run in two things at once and cannot attribute what it finds to entry
        timing alone. It answers a different and still useful question: whether a system with
        this *shape* of holding time, entering at random, would have done as well.
    """
    shape = (draws, len(held))
    holds = fit(held["hold"].to_numpy(), *shape, rng)
    return _lay(holds, fit(market["gaps"] + MIN_HOLD, *shape, rng) - MIN_HOLD,
                market["n_bars"], rng)
