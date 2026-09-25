"""Everything one run of the study reads, assembled once: streams, daily bars, costs, identity."""

from core import barstore, manifest, tradestore
from core.paths import bar_source, export_dir
from core.study import identity
from strategies.monteCarlo.inputs import costs, stream
from strategies.monteCarlo.model import regime
from strategies.monteCarlo.simulate import stability


def load(project: str, databank: str, asset: str, export: str, cfg: dict,
         bars_timeframe: str = "M30", portfolio: bool = False) -> dict:
    """The inputs one.run() and many.run() read.

    Args:
        project, databank: Where the trades were exported from.
        asset: Asset name in assets/, e.g. XAUUSD.
        export: Export date, YYYY-MM-DD.
        cfg: What config.load() returned.
        bars_timeframe: Which bars the daily volatility is built from.
        portfolio: Treat every strategy as one combined trade stream.

    Returns:
        {"streams", "day", "asset", "identity", "shared", "reference"}. The stability check
        runs here, once, on the strategy with the most trades: it measures the simulation
        count, not any one strategy, and it is the costliest thing a single run would redo.
    """
    costs_ = costs.load(asset)
    folder = export_dir(project, databank, export)
    packed = tradestore.read(folder / "trades.parquet")
    # The packed export drops the constant Symbol column, so the feed comes from the
    # manifest — the record of which market the backtest actually ran on.
    feed = manifest.read(folder)["source"]["symbol"]
    risk = cfg["global"]["risk_per_trade"]
    streams = ([stream.portfolio(packed, costs_, risk, databank)] if portfolio else
               [stream.build(f, n, costs_, risk)
                for n, f in tradestore.by_strategy(packed).items()])
    reference = max(streams, key=lambda s: s["pnl"].size)
    names = [s["name"] for s in streams]
    return {"streams": {s["name"]: s for s in streams},
            "day": regime.daily(barstore.read(feed, bars_timeframe)), "asset": costs_,
            "identity": {} if portfolio else identity.lookup(project, databank, names),
            "reference": reference["name"],
            "shared": {"export": folder / "trades.parquet", "bars": bar_source(feed),
                       "stability": stability.spread(reference, cfg)}}
