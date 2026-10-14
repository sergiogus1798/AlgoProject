"""Everything one run of the cross-market study reads, assembled once for the whole export."""

from pathlib import Path
from typing import TypedDict, cast

import pandas as pd

from core import barstore, tradestore
from core.paths import export_dir
from core.study import identity
from studies.transfer.crossmarket.inputs import markets


def within(trades: pd.DataFrame, feeds: list[str]) -> pd.DataFrame:
    """The export cut to each market's own window: no trade outside its build..oos1 is read.

    Args:
        trades: The whole export, `Symbol` naming the market of each trade.
        feeds: Every feed of the universe, base asset included.

    Returns:
        The trades opened on or after their market's own build start and closed by the end
        of its own oos1 (`markets.own_window`); a trade straddling either edge is dropped,
        as `envelope.segment` does. The step-9 task already runs those dates; this is the
        guard for an export written before 2026-10-02, when an extra market ran the MAIN's
        dates and an index main carried gold and USDJPY into their `oos2`. A feed no card
        declares is left whole.
    """
    keep = pd.Series(True, index=trades.index)
    for feed in feeds:
        span = markets.own_window(feed)
        if span:
            end = pd.Timestamp(span["to"]) + pd.Timedelta(days=1)
            keep &= (trades["Symbol"] != feed) | ((trades["Open time"] >= span["from"])
                                                  & (trades["Close time"] < end))
    return cast(pd.DataFrame, trades[keep])


class Inputs(TypedDict):
    """What one.run() and many.run() read: the export, its universe, every feed's bars, names and identities."""

    project: str
    databank: str
    export: str
    asset: str
    path: Path
    universe: markets.Universe
    trades: pd.DataFrame
    strategies: list[str]
    outside: int
    identity: dict[str, str | None]
    bars: dict[str, pd.DataFrame]


def load(project: str, databank: str, asset: str, export: str) -> Inputs:
    """The inputs one.run() and many.run() read.

    Args:
        project: SQX project name.
        databank: The databank export_retest exported.
        asset: Base asset, e.g. "USDJPY".
        export: Export date, YYYY-MM-DD.

    Returns:
        The export, its market universe, every feed's bars, the strategy names on the base
        asset and their identity (`identity.resolve`: installs, cosecha, kept .sqx; None
        where none names it), and `outside`, how many trades `within` left out. The whole
        export is one read: every view slices it with
        `tradestore.market` rather than opening a file per strategy and market.
    """
    packed = export_dir(project, databank, export) / "trades.parquet"
    universe = markets.universe(asset, packed)
    whole = tradestore.read(packed)
    trades = within(whole, markets.feeds(universe))
    names = sorted(trades.loc[trades["Symbol"] == universe["main"], "strategy"].unique())
    return Inputs(project=project, databank=databank, export=export, asset=asset,
                  path=packed, universe=universe, trades=trades, strategies=names,
                  outside=len(whole) - len(trades),
                  identity=identity.resolve(project, databank, names, packed.parent, export),
                  bars={feed: barstore.read(feed, universe["timeframe"])
                        for feed in markets.feeds(universe)})
