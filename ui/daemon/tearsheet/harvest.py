"""One strategy of a databank's newest cosecha: its daily curve, its trades and its SQX metrics."""

from pathlib import Path

import pandas as pd

from core.paths import DATA
from ui.daemon.tearsheet import borrow

SAMPLES = ("IS", "OOS")      # the one-way door: a harvest holds these two and nothing else
EQUITY = ["day", "equity", "sample"]
TRADES = ["Open time", "Close time", "Profit/Loss", "Size", "Balance", "Close type", "MAE ($)",
          "MFE ($)", "sample"]


class Absent(str):
    """A strategy the databank holds that its cosecha does not pair: a fact, not a failure —
    cut before the OOS retest (a «Continuar workflow»), or never retested. Painted grey."""


def newest(project: str, databank: str) -> Path | None:
    """The newest cosecha folder of (project, databank), by its folder date.

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


def read(project: str, databank: str, identity: str, name: str = "") -> dict | str:
    """One strategy's rows of the newest cosecha, filtered on identity at read time.

    Args:
        project, databank: The build databank.
        identity: SHA-256 of the normalised XML, as SELECTION holds it; it pairs only
            inside this databank (knowhow/sqx-format/identity-differs-across-databanks.md).
        name: The strategy's name, for `borrow` when the databank has no cosecha of its own.

    Returns:
        `day`, `folder`, `strategy` (name), `identity`, `metrics` (the SQX row as a dict),
        `equity` and `trades` (DataFrames, ascending in time), the `databank` read and its
        `note` («» unless borrowed from the build's, `borrow`) — or the sentence of why not.
        A sample other than IS/OOS is refused, never filtered out.
    """
    folder, note = newest(project, databank), ""
    if folder is None:
        got = borrow.borrow(project, databank, identity, newest, name)
        if got is None:
            return missing(project, databank)
        if isinstance(got, str):
            return Absent(got)
        databank, identity, note = got
        folder = newest(project, databank)
    where = [("identity", "==", identity)]
    metrics = pd.read_parquet(folder / "metrics.parquet", filters=where)
    if metrics.empty:
        return Absent(f"Sin pareja en el OOS de la cosecha {folder.name}: esta estrategia se "
                      "quedó fuera en un corte («Continuar workflow») o SQX no la retesteó. La "
                      "cosecha solo lleva las que tienen las dos muestras; sus cifras IS siguen "
                      f"en la tabla de {databank}.")
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
            "databank": databank, "note": note, "identity": identity, "metrics": row, "equity": equity.sort_values("day", kind="stable"),
            "trades": trades.sort_values("Close time", kind="stable")}
