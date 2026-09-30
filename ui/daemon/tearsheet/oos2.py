"""OOS2 for the Ficha, read from a cosecha that carries it — sealed until 17-19 only for an autonomous agent (`ledger.gate.enforced`)."""

import pandas as pd

from core.paths import DATA
from ui.daemon.tearsheet.harvest import EQUITY, TRADES
from ui.daemon.workflow import ledgerview

LOCKED = "reservado: se abre tras los pasos 17, 18 y 19"
NO_EXPORT = "OOS2 abierto, sin export: exporta el retest oos2"
NAMES = ["OOS2", "oos2"]        # how a cosecha may spell the sample (plan 24 §10, Q10)


def blocked(project: str) -> dict | None:
    """The step-20 door, asked of the ledger over the study blindJoint reads.

    Args:
        project: Project name.

    Returns:
        `{"blocked": LOCKED, "why": the gate's own sentence}` while sealed, else None.
    """
    door = ledgerview.door(project)
    return {"blocked": LOCKED, "why": door["text"]} if door["sealed"] else None


def read(project: str, identity: str) -> dict | str:
    """The OOS2 rows of one strategy, from the newest cosecha of the project that holds them.

    Called only once `blocked` said open. No cosecha of oos2 exists today (2026-09-28):
    the owner's reading of Q10 is that the Ficha says so rather than pick another source.

    Args:
        project: Project name.
        identity: The strategy's identity inside the databank that was harvested.

    Returns:
        `harvest.read`'s shape with every row's sample «OOS2», or `NO_EXPORT`.
    """
    where = [("identity", "==", identity), ("sample", "in", NAMES)]
    for path in sorted((DATA / "harvest" / project).glob("*/*/equity.parquet"),
                       key=lambda p: p.parent.name, reverse=True):
        equity = pd.read_parquet(path, columns=EQUITY, filters=where)
        if equity.empty:
            continue
        folder = path.parent
        trades = pd.read_parquet(folder / "trades.parquet", columns=TRADES, filters=where)
        metrics = pd.read_parquet(folder / "metrics.parquet", filters=where[:1])
        row = metrics.iloc[0].to_dict() if len(metrics) else {"strategy": ""}
        trades["Close type"] = trades["Close type"].astype(str)
        return {"day": folder.name, "folder": str(folder), "strategy": row["strategy"],
                "identity": identity, "metrics": row,
                "equity": equity.assign(sample="OOS2").sort_values("day", kind="stable"),
                "trades": trades.assign(sample="OOS2").sort_values("Close time", kind="stable")}
    return NO_EXPORT
