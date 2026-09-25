"""Everything one run of the cross-market study reads, assembled once for the whole export."""

from core import barstore, tradestore
from core.paths import export_dir
from core.study import identity
from studies.transfer.crossmarket.inputs import markets


def load(project: str, databank: str, asset: str, export: str) -> dict:
    """The inputs one.run() and many.run() read.

    Args:
        project: SQX project name.
        databank: The databank export_retest exported.
        asset: Base asset, e.g. "USDJPY".
        export: Export date, YYYY-MM-DD.

    Returns:
        The export, its market universe, every feed's bars, the strategy names on the base
        asset and their identity. The whole export is one read: every view slices it with
        `tradestore.market` rather than opening a file per strategy and market.
    """
    packed = export_dir(project, databank, export) / "trades.parquet"
    universe = markets.universe(asset, packed)
    trades = tradestore.read(packed)
    names = sorted(trades.loc[trades["Symbol"] == universe["main"], "strategy"].unique())
    return {"project": project, "databank": databank, "export": export, "asset": asset,
            "path": packed, "universe": universe, "trades": trades, "strategies": names,
            "identity": identity.lookup(project, databank, names),
            "bars": {feed: barstore.read(feed, universe["timeframe"])
                     for feed in markets.feeds(universe)}}
