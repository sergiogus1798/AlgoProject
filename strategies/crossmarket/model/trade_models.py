"""How a random run's trades are drawn: the study's modelling assumptions, and its alternatives.

The registry lives here, and with it the models that randomise **placement only** — the ones
that move each real trade with its own hold. The free-placement family, which re-lays the whole
run anywhere in the window, is in `free_models.py`; that is the split the report argues, so it
is the split the code makes. Every model shares one signature, `(held, market, draws, rng,
batch)` in and `(entries, holds)` out, and declares in RANDOMISES what it changes."""

import numpy as np
import pandas as pd

from strategies.crossmarket.model.free_models import (fitted_holds, resampled_holds,
                                                      segment_permute)


def semester_shift(seed: int, period: int, draws: int, batch: int) -> np.ndarray:
    """The displacement of one calendar semester, identical in every market of the draw.

    Args:
        seed: nulls.seed.
        period: The semester's absolute calendar id, from envelope.periods().
        draws: How many runs this batch produces.
        batch: How many runs were already produced before it, so a chunked run continues the
            same sequence instead of restarting it.

    Returns:
        One fraction in [0, 1) per run, drawn from a generator keyed by the semester itself
        rather than by the market. Each market turns the fraction into whole weeks of its own
        semester, so draw d displaces 2013H1 the same way in Brent and in silver — which is
        what makes a joint null across markets correctly sized. Measured before this existed,
        the correlation between draw d's mean_r on two markets was -0.0016: sharing
        `nulls.seed` couples nothing, because every market consumes its own generator at its
        own shape.
    """
    return np.random.default_rng([seed, period]).random(batch + draws)[batch:, None]


def cut_at_next(entries: np.ndarray, holds: np.ndarray) -> np.ndarray:
    """Cut every hold at the next trade of the same run, the way the Friday close cuts one.

    Args:
        entries: A (runs, trades) array of entry bar indices, columns in the real order.
        holds: Bars held, same shape.

    Returns:
        The holds, each capped so the trade closes at or before the next one opens. The
        strategies are single-position — flat to enter — so a run holding two at once is not
        a counterfactual of anything. Cutting keeps the trade count, which dropping the
        clashing trade does not: measured on Strategy 24.14.35, dropping removed 3-5% of the
        trades of every run and traded an exposure bias for a sample-size one. A hold cut to
        zero drops out of that run exactly as a Friday cut drops one.
    """
    order = np.argsort(entries, axis=1, kind="stable")
    ent, hold = np.take_along_axis(entries, order, 1), np.take_along_axis(holds, order, 1)
    room = np.full(hold.shape, np.iinfo(np.int64).max)
    room[:, :-1] = ent[:, 1:] - ent[:, :-1]
    out = np.empty_like(hold)
    np.put_along_axis(out, order, np.minimum(hold, room), 1)
    return out


def block_shift(held: pd.DataFrame, market: dict, draws: int, rng: np.random.Generator,
                batch: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Move each regime block's real trades by a whole number of weeks inside that block.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned for this market, plus the seed.
        draws: How many runs.
        rng: Seeded generator. **Unused here**: this model's randomness is keyed by the
            calendar so that it is identical across markets, which a sequential generator
            cannot be — every market consumes it at its own shape. The parameter stays
            because it is the registry's contract.
        batch: Runs already produced, for the chunked loop in backtest.drawn().

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

    Two properties were added on 2026-09-17. The displacement of a semester is drawn from
    `semester_shift()`, keyed by the calendar rather than by this market, so one draw is one
    displacement everywhere and `simulate/joint.py` can pool the markets. And the holds
    are re-cut at the next trade: until then 2.8-5.4% of every run's trades opened before
    the previous one had closed, in the one model the summary reports.
    """
    entry = held["entry"].to_numpy()
    block, period, index = market["block"], market["period"], market["calendar"]
    ids = block[entry]
    out = np.empty((draws, entry.size), dtype=np.int64)
    for b in np.unique(ids):
        member = ids == b
        here = entry[member]
        span = index["size"][here].max()
        weeks = (semester_shift(market["seed"], int(period[here[0]]), draws, batch)
                 * span).astype(np.int64)
        rank = index["pos"][here] - index["start"][here]
        out[:, member] = index["order"][index["start"][here]
                                        + (rank + weeks) % index["size"][here]]
    holds = np.repeat(held["hold"].to_numpy()[None, :], draws, axis=0)
    return out, cut_at_next(out, holds)


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
                  rng: np.random.Generator, batch: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Move each real trade, with its own hold, to a random bar of its own regime stratum.

    Args:
        held: What envelope.occupancy() returned.
        market: What backtest.setting() put in `market`; this model reads its `strata`.
        draws: How many runs.
        rng: Seeded generator.
        batch: Runs already produced; unused, this model's randomness is
            sequential. The registry's contract carries it for block_shift.

    Returns:
        Entry indices and holds. The stratum is the volatility quantile times the sign of the
        recent trend, both read before the bar opens (mechanics/strata.py), so the regime is
        held fixed by state rather than by a calendar block of arbitrary length; weekday, hour,
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
