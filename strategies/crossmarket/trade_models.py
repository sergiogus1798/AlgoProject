"""How a random run's trades are drawn: the study's modelling assumptions, and its alternatives."""

import numpy as np
import pandas as pd

from strategies.crossmarket.holdfit import MIN_HOLD, fit


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


def block_shift(held: pd.DataFrame, market: dict, draws: int,
                rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Move each regime block's real trades by a whole number of weeks inside that block.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned for this market.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Entry indices and holds. Randomises the placement and nothing else: the count, the
        holds, the gaps, the clustering, the weekday and the hour are all the real ones. It is
        the only model here under which the real run and the random ones differ in exactly one
        thing, which is why it is the one read first.

    Measured over 8 (strategy, market) pairs with the sample bounded to the backtest's own
    window, it returns the **lowest p in 7 of them** — but not all, and its spread is the
    narrowest in only 5. It is not systematically the conservative choice; it is the
    *attributable* one. An earlier measurement made it look far tighter than it is, because
    the other models were then free to place trades across the whole bar file, a third of
    which lies outside the backtest.
    """
    entry = held["entry"].to_numpy()
    block, index = market["block"], market["calendar"]
    ids = block[entry]
    out = np.empty((draws, entry.size), dtype=np.int64)
    for b in np.unique(ids):
        member = ids == b
        here = entry[member]
        weeks = rng.integers(0, index["size"][here].max(), size=(draws, 1))
        rank = index["pos"][here] - index["start"][here]
        out[:, member] = index["order"][index["start"][here]
                                        + (rank + weeks) % index["size"][here]]
    return out, np.repeat(held["hold"].to_numpy()[None, :], draws, axis=0)


def segment_permute(held: pd.DataFrame, market: dict, draws: int,
                    rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Reorder the real hold-and-gap segments and lay them from a random start bar.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.

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
                    rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Draw holds and gaps with replacement from the real ones, and lay them out.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.

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
                 rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Fit a distribution to the real holds and gaps, and draw new ones from it.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.

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


def _drop_overlaps(entries: np.ndarray, holds: np.ndarray) -> np.ndarray:
    """Zero the hold of every trade that opens inside an earlier trade of the same run.

    Args:
        entries: A (runs, trades) array of entry bar indices, columns in the real order.
        holds: Bars held, same shape.

    Returns:
        The holds, with the later trade of every overlapping pair set to zero. Sorted to find
        the clashes and scattered back, because column k must stay real trade k: the pricer
        charges it that trade's size and cost.
    """
    order = np.argsort(entries, axis=1, kind="stable")
    ent, hold = np.take_along_axis(entries, order, 1), np.take_along_axis(holds, order, 1)
    reach = np.maximum.accumulate(ent + hold, axis=1)
    clash = np.zeros(hold.shape, dtype=bool)
    clash[:, 1:] = ent[:, 1:] < reach[:, :-1]
    out = np.empty_like(hold)
    np.put_along_axis(out, order, np.where(clash, 0, hold), 1)
    return out


def regime_strata(held: pd.DataFrame, market: dict, draws: int,
                  rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Move each real trade, with its own hold, to a random bar of its own regime stratum.

    Args:
        held: What envelope.occupancy() returned.
        market: What backtest.setting() put in `market`; this model reads its `strata`.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Entry indices and holds. The stratum is the volatility quantile times the sign of the
        recent trend, both read before the bar opens (strata.py), so the regime is held fixed
        by state rather than by a calendar block of arbitrary length; the weekday, hour,
        order and clustering are all free. Trades are placed independently, so the later of
        two that land on each other is dropped. Off by default: it runs only when
        `nulls.models` lists it, and the window sweep never uses it.
    """
    entry, index = held["entry"].to_numpy(), market["strata"]
    pick = index["start"][entry] + (rng.random((draws, entry.size))
                                    * index["size"][entry]).astype(np.int64)
    entries = index["order"][pick]
    holds = np.repeat(held["hold"].to_numpy()[None, :], draws, axis=0)
    return entries, _drop_overlaps(entries, holds)


def truncate(entries: np.ndarray, holds: np.ndarray, market: dict) -> np.ndarray:
    """Cut every random hold at the Friday close, the way the real exit rule cuts the real one.

    Args:
        entries: A (runs, trades) array of entry bar indices.
        holds: Bars held, same shape.
        market: What envelope.describe() returned.

    Returns:
        The holds, each capped at the bars remaining to the next Friday close. A hold that
        reaches it exactly becomes zero and its trade drops out of that run — so a run's
        effective trade count varies even though every model draws the same number of them,
        which is why the statistics carry a `live` mask. Applied to every model: under
        block_shift it is close to a no-op, since that model already keeps the weekday and
        hour, and the difference between the two is the holiday weeks.
    """
    return np.minimum(holds, market["friday_cap"][entries])


MODELS = {"block_shift": block_shift, "segment_permute": segment_permute,
          "resampled_holds": resampled_holds, "fitted_holds": fitted_holds,
          "regime_strata": regime_strata}

# What each model holds fixed and what it randomises. A model that randomises more than one
# thing cannot attribute a low p-value to any single cause, which is why the verdict uses
# block_shift and the others are read beside it.
RANDOMISES = {"block_shift": "placement, within the regime block and the weekday-hour slot",
              "segment_permute": "placement, order, clustering and calendar",
              "resampled_holds": "placement, which holds and gaps occur, and time in market",
              "fitted_holds": "placement, and the holding times themselves",
              "regime_strata": "placement, within bars of the same volatility quantile and "
                               "trend sign; frees the weekday, hour and clustering"}
