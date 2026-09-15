"""The mechanical envelope of a strategy on one market: which bars it held, and when it was flat."""

import numpy as np
import pandas as pd


def window(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """The bars the backtest actually covered, from its first entry to its last exit.

    Args:
        trades: One market's real trades, times already parsed.
        bars: That market's whole bar file.

    Returns:
        The slice between the first entry and the last exit, both included. **Every other
        function here takes the slice, never the file.** A bar file runs wider than the
        retest that was run on it — measured, 2003-2026 against a 2008-2022 backtest, so a
        third of the bars sit outside it — and a null model that may place trades anywhere in
        the file is trading years the real strategy never saw. That is not a fair comparison
        in either direction: the extra years carry their own drift and their own volatility
        regime, and the equity axis stretches over a stretch where the real curve is flat by
        construction.
    """
    return bars.loc[trades["Open time"].min():trades["Close time"].max()]


def occupancy(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """Locate every trade on the bar grid.

    Args:
        trades: One market's trades, times already parsed.
        bars: That market's bars, indexed by bar open time.

    Returns:
        Columns entry, exit and hold, in bar indices. Trades whose entry or exit falls outside
        the bar file are dropped: they cannot be repriced and would silently shorten the hold.
    """
    entry = bars.index.get_indexer(trades["Open time"], method="pad")
    out = bars.index.get_indexer(trades["Close time"], method="pad")
    keep = (entry >= 0) & (out > entry)
    return pd.DataFrame({"entry": entry[keep], "exit": out[keep],
                         "hold": out[keep] - entry[keep]}, index=trades.index[keep])


def gaps(held: pd.DataFrame) -> np.ndarray:
    """Flat stretches between consecutive trades, in bars.

    Args:
        held: What occupancy() returned, in chronological order.

    Returns:
        One gap per trade: the bars flat before it, the first counted from the first bar of
        the sample. Holds and gaps together are the marginals every null must preserve, since
        they fix trade density and therefore exposure to the market's own drift.
    """
    entry, exit_ = held["entry"].to_numpy(), held["exit"].to_numpy()
    return np.concatenate([[entry[0]], entry[1:] - exit_[:-1]])


def calendar_index(bars: pd.DataFrame, block: np.ndarray) -> dict[str, np.ndarray]:
    """Group every bar with the bars that share its regime block, weekday and hour.

    Args:
        bars: One market's bars.
        block: One regime-block id per bar, from blocks().

    Returns:
        Arrays order, pos, start and size. Moving a bar by k positions inside its own group is
        moving it k weeks without ever doing calendar arithmetic: the group is built from the
        timestamps that exist, so daylight saving and short holiday weeks cost nothing, and the
        weekday and hour of the entry are preserved exactly rather than approximately. That
        matters because an eight-bar hold entered late on a Friday spans the weekend gap and
        one entered on a Tuesday does not.
    """
    key = block * 168 + bars.index.dayofweek.to_numpy() * 24 + bars.index.hour.to_numpy()
    order = np.argsort(key, kind="stable")
    pos = np.empty(key.size, dtype=np.int64)
    pos[order] = np.arange(key.size)
    ordered = key[order]
    start = np.searchsorted(ordered, key)
    return {"order": order, "pos": pos, "start": start,
            "size": np.searchsorted(ordered, key, side="right") - start}


FRIDAY, FRIDAY_CLOSE = 4, 21   # measured: 832 of 838 "End Of Friday" exits land on Friday 21:00


def friday_cap(bars: pd.DataFrame) -> np.ndarray:
    """Bars from each bar to the next Friday close, which is when an open trade is forced out.

    Args:
        bars: One market's bars.

    Returns:
        One count per bar; the last bars, which no Friday close follows, get the bars left in
        the file. These strategies carry an "End Of Friday (Time)" exit — 5.4% of all trades
        across the sampled databank — so a hold is not a property of the trade alone: the same
        eight-bar intention ends early if it is laid down on a Friday afternoon. A null that
        reuses holds without re-applying this gives its random trades a rule the real one did
        not have.
    """
    closes = np.flatnonzero((bars.index.dayofweek == FRIDAY)
                            & (bars.index.hour == FRIDAY_CLOSE))
    nxt = np.searchsorted(closes, np.arange(len(bars)), side="right")
    return np.where(nxt < len(closes), closes[np.minimum(nxt, len(closes) - 1)],
                    len(bars) - 1) - np.arange(len(bars))


def describe(bars: pd.DataFrame, held: pd.DataFrame, months: int) -> dict:
    """Everything a trade model needs to know about one market and one real run on it.

    Args:
        bars: One market's bars.
        held: What occupancy() returned.
        months: Regime block length in months.

    Returns:
        Keys block, calendar, gaps, n_bars and friday_cap. This is the whole interface
        between the
        envelope and the models: a new model reads this dict and returns entries and holds,
        and needs nothing else from the rest of the study.
    """
    regime = blocks(bars, months)
    return {"block": regime, "calendar": calendar_index(bars, regime),
            "gaps": gaps(held), "n_bars": len(bars), "friday_cap": friday_cap(bars)}


def blocks(bars: pd.DataFrame, months: int) -> np.ndarray:
    """Which regime block each bar belongs to.

    Args:
        bars: One market's bars.
        months: Block length. Six is the default used by the report.

    Returns:
        One block id per bar. The null shifts inside a block rather than across the whole
        sample, because thirteen years of gold are not one regime: a global shift would let a
        strategy whose trades sit in a strong trending stretch beat the null on drift alone.
    """
    period = (bars.index.year * 12 + bars.index.month - 1) // months
    return (period - period.min()).to_numpy()
