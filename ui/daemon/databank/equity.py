"""A databank's aggregate daily P&L: SQX's, and the one at Darwinex's real spread and slippage."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

from core.paths import harvest_dir
from ui.daemon.loader import find
from ui.daemon.loader.state import newest
from ui.daemon.results import store

# The `spread` study's trade column the window calls «real»: both costs, the owner's default
# reading (`reprice.judge`).
REAL = "Profit/Loss spread y slippage reales"


@lru_cache(maxsize=8)
def daily(path: str, stamp: float) -> pd.DataFrame:
    """A cosecha's equity as daily P&L per strategy, one row per identity, sample and day.

    Args:
        path: The cosecha's `equity.parquet`.
        stamp: Its mtime, the cache's version.

    Returns:
        Columns `identity`, `sample`, `day`, `pnl`. Each sample's curve starts at zero (it is
        its own backtest), so its first day's P&L is its first value.
    """
    eq = pd.read_parquet(path).sort_values(["identity", "sample", "day"])
    eq["pnl"] = eq.groupby(["identity", "sample"])["equity"].diff().fillna(eq["equity"])
    return eq[["identity", "sample", "day", "pnl"]]


@lru_cache(maxsize=8)
def correction(path: str, stamp: float) -> pd.DataFrame:
    """What the real spread and slippage change, per strategy, sample and closing day.

    Args:
        path: A `spread` report's `trades.parquet`.
        stamp: Its mtime.

    Returns:
        Columns `identity`, `sample`, `day`, `delta` — the real-cost P&L minus SQX's, summed.
    """
    t = pd.read_parquet(path, columns=["identity", "sample", "Close time", "Profit/Loss", REAL])
    t["day"] = t["Close time"].dt.normalize()
    t["delta"] = t[REAL] - t["Profit/Loss"]
    return t.groupby(["identity", "sample", "day"], as_index=False)["delta"].sum()


def summed(frame: pd.DataFrame, column: str, ids: set[str] | None) -> pd.DataFrame:
    """One column of a per-strategy frame summed by sample and day, over `ids` or every row."""
    if ids is not None:
        frame = frame[frame["identity"].isin(ids)]
    return frame.groupby(["sample", "day"], as_index=False)[column].sum()


def spread_trades(project: str, databank: str) -> Path | None:
    """The newest `spread` report's trades of this databank, or None."""
    days = store.days(project, databank, "spread")
    path = store.bank(project, databank) / days[0] / "spread" / "trades.parquet" if days else None
    return path if path and path.is_file() else None


def drawdown(curve: list[float]) -> float:
    """The worst fall from a peak of a cumulative curve, in money, as a negative number."""
    peak, worst = 0.0, 0.0
    for v in curve:
        peak = max(peak, v)
        worst = min(worst, v - peak)
    return worst


def equity(project: str, databank: str, ids: list[str] | None = None) -> dict:
    """GET /api/databank/equity: the databank's aggregate curves.

    Args:
        project: Project name.
        databank: Either spelling.
        ids: Only these identities (the rows a filter left visible); None for every one.

    Returns:
        `days` (ISO), `sqx` and `real` (cumulative; `real` None when no `spread` report
        exists, with `real_why`), `split` (index of the first OOS day, or None), `stats`,
        `source` and `of` (`todas`, or how many identities were asked). Or `{error}` when
        the databank has no cosecha: the curve needs the daily equity the cosecha carries.
    """
    db = find.spelled(project, databank)
    found = newest(harvest_dir(project, db, "x").parent, "equity.parquet")
    if found is None:
        return {"error": f"{db} no tiene cosecha: la curva agregada sale de su equity diaria "
                         "(la cosecha IS + OOS del paso 8)"}
    wanted = set(ids) if ids is not None else None
    pnl = summed(daily(str(found), found.stat().st_mtime), "pnl", wanted).sort_values(
        ["sample", "day"])                              # «IS» sorts before «OOS»
    if pnl.empty:
        return {"error": "ninguna de las estrategias visibles está en la cosecha"}
    trades = spread_trades(project, db)
    real = None
    if trades is not None:
        fix = summed(correction(str(trades), trades.stat().st_mtime), "delta", wanted)
        both = pnl.merge(fix, on=["sample", "day"], how="outer").fillna(0.0)
        both = both.sort_values(["sample", "day"])
        pnl, real = both, (both["pnl"] + both["delta"]).cumsum().round(2).tolist()
    sqx = pnl["pnl"].cumsum().round(2).tolist()
    oos = (pnl["sample"] == "OOS").tolist()
    split = oos.index(True) if True in oos else None
    net = {s: float(pnl.loc[pnl["sample"] == s, "pnl"].sum()) for s in ("IS", "OOS")}
    stats = {"Neto SQX IS": net["IS"], "Neto SQX OOS": net["OOS"], "Neto SQX": sqx[-1],
             "DD máximo SQX": drawdown(sqx)}
    if real:
        stats |= {"Neto real": real[-1], "DD máximo real": drawdown(real)}
    return {"days": [d.strftime("%Y-%m-%d") for d in pnl["day"]], "sqx": sqx, "real": real,
            "split": split, "stats": stats,
            "source": f"cosecha del {found.parent.name}"
                      + (f" · spread real del {trades.parts[-3]}" if trades else ""),
            "of": "todas" if ids is None else len(wanted),
            "real_why": None if real else "sin informe del estudio spread para este databank"}
