"""The trade library: one Parquet per export, holding only what cannot be derived back."""

from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from core import trades

# What `orderstocsv` writes that is worth storing. The four it leaves out are derivable or
# empty, measured 2026-09-20 on Strategy 1.19.29 (763 trades) and re-measured across five:
# `Ticket` = row order, `Time in trade` = Close − Open (and text), `Comment` all null, and
# `Symbol` constant per file — except under data=all, where it is kept because it names the
# market. It does not separate the blocks on its own: see `pack`. `Balance` is derivable too
# (100k + cumsum) and is kept by the owner's call.
KEEP = ["Type", "Open time", "Open price", "Size", "Close time", "Close price",
        "Profit/Loss", "Balance", "Sample type", "Close type", "MAE ($)", "MFE ($)"]
CATEGORICAL = ("strategy", "Symbol", "Type", "Sample type", "Close type")


def ordered(frame: pd.DataFrame) -> bool:
    """Whether row order alone carries what the ticket said.

    Args:
        frame: One strategy's trades, as core.trades.read() returned them.

    Returns:
        True when the rows are in open-time order, no two trades open at the same instant,
        and none opens before the previous closes. Parquet preserves row order, so under
        those three the ticket is the file itself. A pyramiding strategy breaks the second
        and `Ticket` has to be kept for it — core.tradepack.pack() checks rather than assumes.
    """
    opens, closes = frame["Open time"], frame["Close time"]
    return bool(opens.is_monotonic_increasing and not opens.duplicated().any()
                and (opens.iloc[1:].to_numpy() >= closes.iloc[:-1].to_numpy()).all())


def blocks_of(frame: pd.DataFrame) -> pd.Series:
    """Which result block each row of a data=all export belongs to.

    Args:
        frame: One strategy's export, in the row order orderstocsv wrote it.

    Returns:
        A block index per row, 0 for the main test. Every block numbers its tickets from
        1, so the k-th row carrying a given ticket belongs to the k-th block.

    🔬 2026-09-23: the blocks are NOT contiguous in the CSV. A cross-timeframe export
    comes out ordered by open time with the blocks interleaved, so the old separator —
    a new block wherever the ticket stopped increasing — cut one strategy into 173 pieces
    and `block(packed, s, 0)` returned a sliver of the main test with nothing failing.
    """
    return frame.groupby("Ticket").cumcount()


def whole(frame: pd.DataFrame) -> bool:
    """Whether every block came out as a complete ticket run.

    Args:
        frame: One strategy's export, with `block` already assigned.

    Returns:
        True when each block holds tickets 1..N with no gaps, which is what makes the
        k-th-occurrence rule sound. A False here means the blocks are guesses.
    """
    sizes = frame.groupby("block")["Ticket"]
    return bool(np.all(sizes.max() == sizes.size()) and np.all(sizes.min() == 1))


def _prepared(path: Path, per_market: bool) -> tuple:
    """One strategy's CSV as it goes into the store.

    Args:
        path: A CSV orderstocsv wrote.
        per_market: As in `pack`.

    Returns:
        (frame with the stored columns and its `strategy`, whether it kept `Ticket`,
        whether its market blocks came out torn).
    """
    got = trades.read(path)
    torn = False
    if per_market:
        got["block"] = blocks_of(got)
        torn = not whole(got)
    keep = KEEP + (["Symbol", "block"] if per_market else [])
    keep = keep if ordered(got) else keep + ["Ticket"]
    return got[keep].assign(strategy=path.stem), "Ticket" in keep, torn


def by_strategy(packed: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split a packed export into one frame per strategy.

    Args:
        packed: What read() returned for a whole export.

    Returns:
        {strategy name: its trades}, in the order they were packed. Splitting one read beats
        reading one file per strategy: the whole 757-strategy export loads in 0.16 s.
    """
    return {str(n): g.reset_index(drop=True)
            for n, g in packed.groupby("strategy", sort=False, observed=True)}


def read(path: Path, strategy: str = "") -> pd.DataFrame:
    """One strategy's trades, or every trade of the export.

    Args:
        path: A Parquet written by core.tradepack.pack().
        strategy: Which strategy to read; empty for all of them.

    Returns:
        The same frame core.trades.read() returns, plus a `strategy` column, minus the
        columns core.tradepack.pack() dropped. Row order is the order SQX wrote, which is
        the ticket. The text columns stay categorical: widening them to object costs 326 MB
        against 74 MB on a 960,705-trade export, and nothing downstream needs object dtype — `.to_numpy()`
        and `core.trades.cost()` both handle a category.
    """
    filters = [("strategy", "==", strategy)] if strategy else None
    return pd.read_parquet(path, filters=filters).reset_index(drop=True)


def market(packed: pd.DataFrame, strategy: str, feed: str) -> pd.DataFrame:
    """One strategy's trades on one market, out of a `data=all` export packed per market.

    Args:
        packed: What read() returned for a whole per-market export.
        strategy: Strategy name.
        feed: SQX symbol of the market, as the `Symbol` column spells it.

    Returns:
        The rows, re-indexed from zero, without the `strategy` column. Empty when the
        strategy never fired on that market -- which is a result about the strategy, and
        the caller shows it rather than treating it as a missing input.
    """
    rows = packed[(packed["strategy"] == strategy) & (packed["Symbol"] == feed)]
    return cast(pd.DataFrame, rows.drop(columns=["strategy"]).reset_index(drop=True))


def block(packed: pd.DataFrame, strategy: str, index: int) -> pd.DataFrame:
    """One strategy's trades on one result block of a `data=all` export.

    The block index is what `market()` cannot do when the additional markets share a
    symbol: 0 is the main test and 1.. are the additional markets in the order their
    `<Setup>` elements appear in the retest task.

    Args:
        packed: What read() returned for a whole per-market export.
        strategy: Strategy name.
        index: Position of the block.

    Returns:
        The rows, re-indexed from zero, without the `strategy` column.
    """
    rows = packed[(packed["strategy"] == strategy) & (packed["block"] == index)]
    return cast(pd.DataFrame, rows.drop(columns=["strategy"]).reset_index(drop=True))
