"""The unperturbed trade list each strategy actually produced, read from its own harvest."""

from pathlib import Path

import pandas as pd
import pyarrow as pa

from core import assets, sqxfile, trades as core_trades
from core.paths import harvest_dir

KEEP = ["strategy", "Type", "Open time", "Close time", "Size", "cost", "pnl"]


def feed_of(path: Path) -> tuple[str, str, str]:
    """Asset symbol, its `core.barstore` feed key and the timeframe, off one strategy.

    Args:
        path: Any .sqx of the project -- every strategy of one project runs on the same feed.

    Returns:
        (symbol, feed, timeframe), e.g. ("USDJPY", "USDJPY_M1", "H1"). `sqxfile.symbol()`
        returns the feed with the `_LOM_<timeframe>` suffix SQX appends for its own fill model;
        cutting it there is what turns it into the directory name `core.barstore` actually
        holds, and what is cut off is the grid the strategy trades on.
    """
    symbol, fed = sqxfile.symbol(path)
    feed, _, timeframe = fed.partition("_LOM_")
    return symbol, f"{symbol}_{feed}", timeframe


def newest_harvest(project: str, databank: str) -> Path:
    """The most recently harvested day of one project's build databank.

    Args:
        project: SQX project name.
        databank: The build databank `studies.screening.gate.harvest` paired, e.g. "Results".

    Returns:
        Its directory. Asserts one exists: a Monte Carlo Retest without its project's own
        harvest cannot price a benchmark, and running one first is the fix, not a fallback.
    """
    root = harvest_dir(project, databank, "x").parent
    days = sorted(d for d in root.glob("*") if (d / "trades.parquet").exists())
    assert days, (f"no harvest under {root}; run "
                 f"`python3 -m studies.screening.gate.harvest --project {project} "
                 f"--databank {databank} ...` first")
    return days[-1]


def read(project: str, harvest_databank: str, identities: dict[str, str],
         point_value: float, sample: str = "OOS") -> pd.DataFrame:
    """This ingest's own strategies, priced from their harvest's trade list.

    Args:
        project: SQX project name.
        harvest_databank: The build databank the harvest paired, e.g. "Results".
        identities: {strategy: identity}, from any task's provenance -- a perturbation
            never rewrites a strategy's rules, so its identity is the harvest's own join key.
        point_value: Account currency per 1.0 of price per 1.0 lot (`core.assets`), for the
            cost `core.trades.cost()` recovers.
        sample: "OOS", or "IS" for the build's own trades: the backtest the `bar` and `ohlc`
            tasks perturb, whose dates T2 and T3 need (`measure/excess.py`) and nothing else
            may read.

    Returns:
        One row per **out-of-sample** trade of the strategies this ingest covers, `KEEP`
        only -- `gate.harvest` tags every trade `sample` "IS" or "OOS", and the strategy was
        selected on the "IS" side, so `run.benchmarks()`'s random-entry comparison may only
        read the "OOS" one (owner, 2026-09-29): a footprint priced on the build would score
        the search, not the edge. A strategy the MC Retest tasks ran but the harvest never
        paired (dropped OOS, `studies.screening.gate`) is silently absent -- the caller has
        no window to benchmark it against either.
    """
    by_identity = {identity: strategy for strategy, identity in identities.items()}
    # Only this ingest's rows and the columns `cost` and KEEP read: the harvest holds 10,000 strategies.
    got = pd.read_parquet(newest_harvest(project, harvest_databank) / "trades.parquet",
                          columns=["identity", "sample", "Type", "Open time", "Close time", "Size",
                                   "Open price", "Close price", "Profit/Loss"],
                          filters=[("identity", "in", pa.array(sorted(by_identity), pa.string())), ("sample", "==", sample)])
    got["strategy"] = got["identity"].map(by_identity)
    got["cost"] = core_trades.cost(got, point_value)
    got["pnl"] = got["Profit/Loss"]
    return got[KEEP].reset_index(drop=True)


def asset_point_value(symbol: str) -> float:
    """The one number `core.trades.cost()` needs, from the asset's own file.

    Args:
        symbol: Asset name in assets/, e.g. "XAUUSD".

    Returns:
        Account currency per 1.0 of price per 1.0 lot.
    """
    return float(assets.load(symbol)["instrument"]["point_value"])
