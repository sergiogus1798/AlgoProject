"""One strategy of a databank's newest cosecha: its daily curve, its trades and its SQX metrics."""

from pathlib import Path

import pandas as pd

from core.paths import DATA

SAMPLES = ("IS", "OOS")      # the one-way door: a harvest holds these two and nothing else
EQUITY = ["day", "equity", "sample"]
TRADES = ["Open time", "Close time", "Profit/Loss", "Balance", "Close type", "MAE ($)",
          "MFE ($)", "sample"]


def newest(project: str, databank: str) -> Path | None:
    """The newest cosecha folder of (project, databank), as `gateview.harvests()` dates them.

    Args:
        project, databank: Where the build databank lives.

    Returns:
        `harvest/<P>/<D>/<day>/`, or None when nobody harvested it.
    """
    found = sorted((DATA / "harvest" / project / databank).glob("*/metrics.parquet"))
    return found[-1].parent if found else None


def missing(project: str, databank: str) -> str:
    """The sentence for a databank without a cosecha, naming the command that makes one."""
    return (f"El databank {databank} de {project} no tiene cosecha. La hace "
            f"`python3 -m studies.screening.gate.harvest --project {project} --databank "
            f"{databank} --oos-databank <databank OOS>` (skill /oos-gate).")


def read(project: str, databank: str, identity: str) -> dict | str:
    """One strategy's rows of the newest cosecha, filtered on identity at read time.

    Args:
        project, databank: The build databank.
        identity: SHA-256 of the normalised XML, as SELECTION holds it; it pairs only
            inside this databank (knowhow/sqx-format/identity-differs-across-databanks.md).

    Returns:
        `day`, `folder`, `strategy` (name), `identity`, `metrics` (the SQX row as a dict),
        `equity` and `trades` (DataFrames, ascending in time) — or the Spanish sentence of why not.
        A sample other than IS/OOS is refused, never filtered out.
    """
    folder = newest(project, databank)
    if folder is None:
        return missing(project, databank)
    where = [("identity", "==", identity)]
    metrics = pd.read_parquet(folder / "metrics.parquet", filters=where)
    if metrics.empty:
        return (f"La estrategia {identity[:12]}… no está en la cosecha {folder.name} de "
                f"{project}/{databank}: una identidad solo empareja dentro de su databank.")
    equity = pd.read_parquet(folder / "equity.parquet", columns=EQUITY, filters=where)
    trades = pd.read_parquet(folder / "trades.parquet", columns=TRADES, filters=where)
    stray = (set(equity["sample"]) | set(trades["sample"].astype(str))) - set(SAMPLES)
    if stray:
        return (f"La cosecha {folder.name} de {project}/{databank} trae muestras "
                f"{sorted(stray)} además de IS y OOS: la ficha se niega a leerla.")
    trades["Close type"] = trades["Close type"].astype(str)
    trades["sample"] = trades["sample"].astype(str)
    row = metrics.iloc[0].to_dict()
    return {"day": folder.name, "folder": str(folder), "strategy": row["strategy"],
            "identity": identity, "metrics": row, "equity": equity.sort_values("day", kind="stable"),
            "trades": trades.sort_values("Close time", kind="stable")}
