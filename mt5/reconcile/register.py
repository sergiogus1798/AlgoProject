"""The register of live EAs: which magic number on which firm's account is which strategy."""

from pathlib import Path

import pandas as pd

from core import fleetpaths, sqxfile
from mt5.fleet import magics

COLUMNS = ["magic", "strategy", "identity", "sqx", "firm", "since"]
TIMEFRAMES = {"M1", "M5", "M15", "M30", "H1", "H4", "D1"}


def read() -> pd.DataFrame:
    """The register, generated from the fleet's magics.csv and the owner's workbook — never a second file.

    Returns:
        One row per live EA (`COLUMNS`), `since` as a Timestamp. Refused in Spanish when the
        fleet has no magics.csv yet or no workbook; a magic used twice on one firm stops here:
        its deals could not be told apart.
    """
    if not (magics.path().exists() and fleetpaths.workbook().exists()):
        raise SystemExit(
            f"falta el registro de magics de la flota: {magics.path()} (y el Excel "
            f"{fleetpaths.workbook().name}). Se crea con `python3 -m mt5.fleet.magics --write`; "
            "de él sale la lista de EAs en real, con su magic, identidad, .sqx y empresa."
        )
    rows = magics.register_rows(magics.fill(fleetpaths.workbook(), False))
    rows = rows.astype({"magic": int, "identity": str}).assign(
        since=lambda d: pd.to_datetime(d["since"])
    )
    twice = rows[rows.duplicated(["firm", "magic"], keep=False)]
    if len(twice):
        raise SystemExit(
            "magic repetido en la misma empresa — "
            + ", ".join(f"{r.firm}/{r.magic}" for r in twice.itertuples())  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names
        )
    return rows


def live_in(rows: pd.DataFrame, end: pd.Timestamp) -> pd.DataFrame:
    """The EAs already live before a week ends."""
    return rows[rows["since"] < end].reset_index(drop=True)  # pyright: ignore[reportReturnType]  # pandas/numpy stubs lose the type through indexing


def market(sqx: Path) -> tuple[str, str]:
    """The asset and timeframe a strategy trades, from its own file's entry names."""
    name, rest = sqxfile.symbol(sqx)
    timeframe = rest.rsplit("_", 1)[-1]
    if timeframe not in TIMEFRAMES:
        raise SystemExit(f"{sqx.name}: timeframe «{timeframe}» no reconocido")
    return name, timeframe
