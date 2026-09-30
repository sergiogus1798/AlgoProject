"""A databank's IS+OOS1 figures, from its cosecha's trades: the union SQX's export does not carry."""

from functools import lru_cache

import pandas as pd

from core.paths import harvest_dir
from ui.daemon.loader import find
from ui.daemon.loader.state import newest

# The SQX metrics a union of the IS and OOS1 trades reproduces with SQX's own definition.
# 🔬 2026-09-28 on Test_USDJPY_donchianUpperCrossUp_M30/Results (200 strategies), on the IS
# trades against `[IS]`: trades and Drawdown exact, net within 0.004, PF and Ret/DD within
# SQX's two-decimal rounding, Winning Percent within 0.005 — once the zero-P&L trades are left
# out of its denominator (counted in, it was off by up to 0.29 points; the half-win rule of
# knowhow/columns/zero-pl-trades.md by up to 0.013).
UNION = ("Net profit", "# of trades", "Profit factor", "Winning Percent", "Drawdown",
         "Ret/DD Ratio")
NO_HARVEST = "sin cosecha: la unión IS+OOS1 sale de sus operaciones"


def figures(pnl: pd.Series) -> dict:
    """UNION's figures of one strategy's trades, in closing order.

    Args:
        pnl: Profit/Loss per trade, IS first then OOS1, each in closing order.

    Returns:
        Metric → value; a PF without a losing trade and a Ret/DD without a drawdown are None.
    """
    curve = pnl.cumsum()
    dd = float((curve.cummax().clip(lower=0) - curve).max())
    loss, net = -pnl[pnl < 0].sum(), float(pnl.sum())
    decided = int((pnl != 0).sum())
    return {"Net profit": net, "# of trades": len(pnl),
            "Profit factor": float(pnl[pnl > 0].sum() / loss) if loss > 0 else None,
            "Winning Percent": float((pnl > 0).sum() / decided * 100) if decided else None,
            "Drawdown": dd, "Ret/DD Ratio": net / dd if dd > 0 else None}


@lru_cache(maxsize=4)
def union(path: str, stamp: float) -> dict:
    """Every strategy's IS+OOS1 figures from one cosecha's `trades.parquet`.

    Args:
        path: The cosecha's trades.
        stamp: Its mtime, the cache's version.

    Returns:
        `rows` identity → UNION's figures; `no_oos`, the strategies with IS trades and no OOS
        one (their union would be their IS alone); `oos`, the span SQX wrote in the OOS
        trades' `Sample type` (OOS1, OOS2) or None when it names none or several; `why` when
        that span is not OOS1 and so no union is given.
    """
    t = pd.read_parquet(path, columns=["identity", "sample", "Sample type", "Close time",
                                       "Profit/Loss"])
    t = t[t["sample"].isin(["IS", "OOS"])]
    spans = set(t.loc[t["sample"] == "OOS", "Sample type"].astype(str).unique())
    oos = next(iter(spans)) if len(spans) == 1 and spans <= {"OOS1", "OOS2"} else None
    held = {s: set(t.loc[t["sample"] == s, "identity"]) for s in ("IS", "OOS")}
    no_oos = sorted(held["IS"] - held["OOS"])
    if oos != "OOS1":
        return {"rows": {}, "no_oos": no_oos, "oos": oos,
                "why": f"el OOS de esta cosecha es {', '.join(sorted(spans)) or 'desconocido'}, "
                       "no OOS1: no hay unión IS+OOS1 que calcular"}
    t = t[t["identity"].isin(held["IS"] & held["OOS"])]
    t = t.sort_values(["identity", "sample", "Close time"], kind="stable")
    return {"rows": {k: figures(g["Profit/Loss"].reset_index(drop=True))
                     for k, g in t.groupby("identity", sort=False)},
            "no_oos": no_oos, "oos": oos, "why": None}


def segments(project: str, databank: str) -> dict:
    """GET /api/databank/segments: what the column chooser adds beyond the table's own columns.

    Args:
        project: Project name.
        databank: Either spelling.

    Returns:
        `union` — the metrics computed for IS+OOS1 —, `rows` {identity: {metric: value}},
        `no_oos`, `oos` (which span the OOS block is, None when the data does not say),
        `source` (the cosecha's day), and `why` when there is no union to give.
    """
    db = find.spelled(project, databank)
    found = newest(harvest_dir(project, db, "x").parent, "trades.parquet")
    if found is None:
        return {"union": list(UNION), "rows": {}, "no_oos": [], "oos": None, "source": "",
                "why": NO_HARVEST}
    return {"union": list(UNION), **union(str(found), found.stat().st_mtime),
            "source": f"operaciones de la cosecha del {found.parent.name}"}
