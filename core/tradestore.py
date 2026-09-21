"""The trade library: one Parquet per export, holding only what cannot be derived back."""

from pathlib import Path

import pandas as pd

from core import trades

# What `orderstocsv` writes that is worth storing. The four it leaves out are derivable or
# empty, measured 2026-09-20 on Strategy 1.19.29 (763 trades) and re-measured across five:
# `Ticket` = row order, `Time in trade` = Close − Open (and text), `Comment` all null, and
# `Symbol` constant per file — except under data=all, where it separates the market blocks
# and is kept. `Balance` is derivable too (100k + cumsum) and is kept by the owner's call.
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
        and `Ticket` has to be kept for it — pack() checks rather than assumes.
    """
    opens, closes = frame["Open time"], frame["Close time"]
    return bool(opens.is_monotonic_increasing and not opens.duplicated().any()
                and (opens[1:].to_numpy() >= closes[:-1].to_numpy()).all())


def pack(files: list[Path], out: Path, per_market: bool) -> dict:
    """Every strategy of one export as a single typed Parquet.

    Args:
        files: One CSV per strategy, as orderstocsv wrote them.
        out: Parquet file to write.
        per_market: True for a data=all export, whose CSVs carry several markets and where
            `Symbol` is the only separator between them.

    Returns:
        Counts and the names of any strategy whose row order does not carry its ticket, so
        the manifest records which files kept `Ticket` instead of dropping it.
    """
    columns = KEEP + (["Symbol"] if per_market else [])
    frames, unordered = [], []
    for f in files:
        frame = trades.read(f)
        keep = columns if ordered(frame) else columns + ["Ticket"]
        if "Ticket" in keep:
            unordered.append(f.stem)
        frames.append(frame[keep].assign(strategy=f.stem))
    packed = pd.concat(frames, ignore_index=True)
    for c in CATEGORICAL:
        if c in packed:
            packed[c] = packed[c].astype("category")
    out.parent.mkdir(parents=True, exist_ok=True)
    packed.to_parquet(out, compression="zstd", index=False)
    return {"strategies": len(files), "trades": len(packed),
            "columns": list(packed.columns), "kept_ticket": unordered}


def names(path: Path) -> list[str]:
    """Which strategies one packed export holds.

    Args:
        path: A Parquet written by pack().

    Returns:
        Strategy names, sorted. Reads the one column rather than the file.
    """
    return sorted(pd.read_parquet(path, columns=["strategy"])["strategy"].unique())


def by_strategy(packed: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split a packed export into one frame per strategy.

    Args:
        packed: What read() returned for a whole export.

    Returns:
        {strategy name: its trades}, in the order they were packed. Splitting one read beats
        reading one file per strategy: the whole 757-strategy export loads in 0.16 s.
    """
    return {n: g.reset_index(drop=True)
            for n, g in packed.groupby("strategy", sort=False, observed=True)}


def read(path: Path, strategy: str = "") -> pd.DataFrame:
    """One strategy's trades, or every trade of the export.

    Args:
        path: A Parquet written by pack().
        strategy: Which strategy to read; empty for all of them.

    Returns:
        The same frame core.trades.read() returns, plus a `strategy` column, minus the
        columns pack() dropped. Row order is the order SQX wrote, which is the ticket. The
        text columns stay categorical: widening them to object costs 326 MB against 74 MB
        on a 960,705-trade export, and nothing downstream needs object dtype — `.to_numpy()`
        and `core.trades.cost()` both handle a category.
    """
    filters = [("strategy", "==", strategy)] if strategy else None
    return pd.read_parquet(path, filters=filters).reset_index(drop=True)
