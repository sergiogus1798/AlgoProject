"""The unperturbed trade list each strategy actually produced, read from its own harvest."""

from pathlib import Path

import pandas as pd

from core import assets, sqxfile, trades as core_trades
from core.paths import harvest_dir

KEEP = ["strategy", "Type", "Open time", "Close time", "Size", "cost"]


def feed_of(path: Path) -> tuple[str, str]:
    """Asset symbol and its `core.barstore` feed key, off one strategy of the databank.

    Args:
        path: Any .sqx of the project -- every strategy of one project runs on the same feed.

    Returns:
        (symbol, feed), e.g. ("USDJPY", "USDJPY_DukasM1_the5ers"). `sqxfile.symbol()` returns
        the feed with the `_LOM_<timeframe>` suffix SQX appends for its own fill model; cutting
        it there is what turns it into the directory name `core.barstore` actually holds.
    """
    symbol, fed = sqxfile.symbol(path)
    return symbol, f"{symbol}_{fed.split('_LOM_')[0]}"


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
         point_value: float) -> pd.DataFrame:
    """This ingest's own strategies, priced from their harvest's trade list.

    Args:
        project: SQX project name.
        harvest_databank: The build databank the harvest paired, e.g. "Results".
        identities: {strategy: identity}, from the stress task's provenance -- a perturbation
            never rewrites a strategy's rules, so its identity is the harvest's own join key.
        point_value: Account currency per 1.0 of price per 1.0 lot (`core.assets`), for the
            cost `core.trades.cost()` recovers.

    Returns:
        One row per trade of the strategies this ingest covers, `KEEP` only. A strategy the
        MC Retest tasks ran but the harvest never paired (dropped OOS, `studies.screening.gate`)
        is silently absent -- the caller has no window to benchmark it against either.
    """
    frame = pd.read_parquet(newest_harvest(project, harvest_databank) / "trades.parquet")
    by_identity = {identity: strategy for strategy, identity in identities.items()}
    got = frame[frame["identity"].isin(by_identity)].copy()
    got["strategy"] = got["identity"].map(by_identity)
    got["cost"] = core_trades.cost(got, point_value)
    return got[KEEP].reset_index(drop=True)


def asset_point_value(symbol: str) -> float:
    """The one number `core.trades.cost()` needs, from the asset's own file.

    Args:
        symbol: Asset name in assets/, e.g. "XAUUSD".

    Returns:
        Account currency per 1.0 of price per 1.0 lot.
    """
    return float(assets.load(symbol)["instrument"]["point_value"])
