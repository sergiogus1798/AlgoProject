"""The window sweep: the free-placement models re-drawn inside consecutive calendar blocks."""

import numpy as np
import pandas as pd

from strategies.crossmarket import envelope, trade_models

FULL = "full"


def months(window: str) -> int | None:
    """A sweep window's length in months.

    Args:
        window: "full", or a count and a unit — "6m", "1y", "3y".

    Returns:
        The months, or None for "full", which is the whole backtest window as one block.
    """
    if window == FULL:
        return None
    return int(window[:-1]) * {"m": 1, "y": 12}[window[-1]]


def ordered(windows: list[str]) -> list[str]:
    """The sweep's windows widest first, so a curve reads left to right as regime is handed back.

    Args:
        windows: cfg["sweep"]["windows"], in any order.

    Returns:
        The same labels, "full" first.
    """
    return sorted(windows, key=lambda w: months(w) or float("inf"), reverse=True)


def partition(bars: pd.DataFrame, window: str) -> np.ndarray:
    """Which block of one window size each bar belongs to.

    Args:
        bars: One market's bars, sliced to the backtest window.
        window: A sweep window.

    Returns:
        One id per bar, rising with time. "full" is a single block; any other size is
        envelope.blocks()' calendar blocks, so "6m" is exactly the partition block_shift moves
        trades inside. The first and last blocks are usually partial, which is what the power
        check in inference.sweep_power() is for.
    """
    span = months(window)
    return np.zeros(len(bars), dtype=np.int64) if span is None else envelope.blocks(bars, span)


def bar_hours(bars: pd.DataFrame) -> float:
    """Hours per bar, so block sizes read in H1-equivalent bars whatever the timeframe.

    Args:
        bars: One market's bars.

    Returns:
        The median spacing between bar opens, in hours: 0.5 on M30.
    """
    return float(np.median(np.diff(bars.index.values)) / np.timedelta64(1, "h"))


def blocks(held: pd.DataFrame, block: np.ndarray, index: pd.DatetimeIndex,
           hours: float) -> list[dict]:
    """Every block of one partition: its span, its real trades and the room left to move them.

    Args:
        held: What envelope.occupancy() returned.
        block: What partition() returned.
        index: The bars' timestamps.
        hours: What bar_hours() returned.

    Returns:
        One dict per block, in time order: first and last date, then bars, occupied and free
        in H1-equivalent bars, the real trades whose entry fell inside, and free_share — the
        fraction of the block's bars no real trade held. Holds are capped at the block's end,
        the way confine() caps them. A block with no trade is listed too.
    """
    entry = held["entry"].to_numpy()
    ids = np.unique(block)
    starts, ends = np.searchsorted(block, ids), np.searchsorted(block, ids, side="right")
    of = np.searchsorted(ids, block[entry])
    occupied = np.bincount(of, np.minimum(held["hold"].to_numpy(), ends[of] - entry),
                           ids.size)
    trades = np.bincount(of, minlength=ids.size)
    return [{"start": str(index[a].date()), "end": str(index[b - 1].date()),
             "bars": float((b - a) * hours), "occupied": float(o * hours),
             "free": float((b - a - o) * hours), "trades": int(t),
             "free_share": float(1 - o / (b - a))}
            for a, b, o, t in zip(starts, ends, occupied, trades)]


def confine(model: str, held: pd.DataFrame, block: np.ndarray, draws: int,
            rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Draw one free-placement model inside every block of a partition separately.

    Args:
        model: segment_permute, resampled_holds or fitted_holds. block_shift already fixes the
            regime and needs no confining.
        held: What envelope.occupancy() returned.
        block: What partition() returned.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Entry indices and holds, columns in the real trades' order. Each block's real trades
        — those whose entry fell inside it, holds capped at its end — are handed to the model
        as if the block were the whole window, and the result is shifted to where the block
        starts. The model's own logic draws the holds and gaps, and trade_models._lay keeps
        them inside the block and off each other. Shrinking the block therefore changes one
        thing: how far from its real date a trade may land. With one block this *is* the
        model, draw for draw; tests/test_sweep.py holds that.
    """
    entry, hold = held["entry"].to_numpy(), held["hold"].to_numpy()
    ids = block[entry]
    entries = np.empty((draws, entry.size), dtype=np.int64)
    holds = np.empty((draws, entry.size), dtype=np.int64)
    for b in np.unique(ids):
        member = ids == b
        first, last = np.searchsorted(block, b), np.searchsorted(block, b, side="right")
        local = entry[member] - first
        capped = np.minimum(hold[member], last - first - local)
        sub = pd.DataFrame({"entry": local, "exit": local + capped, "hold": capped})
        drawn = trade_models.MODELS[model](
            sub, {"gaps": envelope.gaps(sub), "n_bars": last - first}, draws, rng)
        entries[:, member], holds[:, member] = drawn[0] + first, drawn[1]
    return entries, holds
