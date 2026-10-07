"""A databank's aggregate daily P&L: SQX's."""

from functools import lru_cache

import pandas as pd

from core.paths import harvest_dir
from ui.daemon.loader import find
from ui.daemon.loader.state import newest


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


def summed(frame: pd.DataFrame, column: str, ids: set[str] | None) -> pd.DataFrame:
    """One column of a per-strategy frame summed by sample and day, over `ids` or every row."""
    if ids is not None:
        frame = frame[frame["identity"].isin(ids)]
    return frame.groupby(["sample", "day"], as_index=False)[column].sum()


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
        `days` (ISO), `sqx` (cumulative), `split` (index of the first OOS day, or None), `stats`,
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
    sqx = pnl["pnl"].cumsum().round(2).tolist()
    oos = (pnl["sample"] == "OOS").tolist()
    split = oos.index(True) if True in oos else None
    net = {s: float(pnl.loc[pnl["sample"] == s, "pnl"].sum()) for s in ("IS", "OOS")}
    stats = {"Neto SQX IS": net["IS"], "Neto SQX OOS": net["OOS"], "Neto SQX": sqx[-1],
             "DD máximo SQX": drawdown(sqx)}
    return {"days": [d.strftime("%Y-%m-%d") for d in pnl["day"]], "sqx": sqx,
            "split": split, "stats": stats, "source": f"cosecha del {found.parent.name}",
            "of": "todas" if ids is None else len(wanted)}
