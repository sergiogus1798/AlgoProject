"""A test databank's strategy read from a cosecha of the project — same XML first, else by name — and said so."""

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from core.paths import DATA
from ui.daemon.loader import find
from ui.daemon.results.hits import aliases


def harvests(project: str) -> list[str]:
    """The project's databanks that carry a cosecha (a workflow project has one: its build)."""
    top = DATA / "harvest" / project
    if not top.is_dir():
        return []
    return sorted(d.name for d in top.iterdir() if any(d.glob("*/metrics.parquet")))


def _rows(folder: Path, column: str, values: list[str]) -> pd.DataFrame:
    """The (strategy, identity) rows of one cosecha whose `column` is one of `values`."""
    return pd.read_parquet(folder / "metrics.parquet", columns=["strategy", "identity"],
                           filters=[(column, "in", values)]).reset_index()


def borrow(project: str, databank: str, identity: str,
           newest: Callable[[str, str], Path | None],
           name: str = "") -> tuple[str, str, str] | str | None:
    """Where a databank without a cosecha finds this strategy: the same XML in any cosecha of
    the project, else the same name.

    Cross Market, Cross TF, MC Retest, SPP, WFM… retest the build's strategies and are never
    harvested. The MC Retest ingest keeps the build's identity, so the same XML is looked for
    first (📓 2026-10-01: «no tiene cosecha» opened from MCR_All beside a Results cosecha that
    holds it); the others carry a new identity (knowhow sqx-format/identity-differs-across-
    databanks), so then the pairing is by name — the databank's own, else the one the page
    gives — and the page says it.

    Args:
        project, databank, identity: The strategy as the page holds it.
        newest: `harvest.newest`, passed to keep the two modules one-way.
        name: The strategy's name as the page shows it, used when the databank's own files
            do not name this identity (`MCR_All` is an ingest, not an SQX databank).

    Returns:
        (the cosecha's databank, the strategy's identity there, the note for the page); a
        sentence when the name is in none or twice; None when there is nothing to borrow
        (no other cosecha, or no name to pair by).
    """
    homes = [h for h in harvests(project) if h != databank.replace(" ", "_")]
    for home in homes:
        if len(_rows(newest(project, home), "identity", [identity])):
            return home, identity, (f"{databank} no tiene cosecha: esta ficha es la de la "
                                    f"cosecha de {home}, la misma estrategia (mismo XML).")
    name = find.roster(project, databank).get(identity) or name
    if not (homes and name):
        return None
    for home in homes:
        found = _rows(newest(project, home), "strategy", aliases(name))
        if len(found) > 1:
            return (f"La cosecha de {home} tiene {len(found)} «{name}»: ábrela desde la Puerta "
                    "IS/OOS")
        if len(found) == 1:
            return home, found["identity"].iloc[0], (
                f"{databank} no tiene cosecha: esta ficha es la de «{name}» en la cosecha de "
                f"{home}, emparejada por nombre (la identidad cambia entre databanks).")
    return f"«{name}» no está en la cosecha de {', '.join(homes)}: se quedó fuera en un corte"
