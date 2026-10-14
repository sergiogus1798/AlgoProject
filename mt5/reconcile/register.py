"""The register of live EAs: which magic number on which firm's account is which strategy."""

from pathlib import Path

import pandas as pd

from core import sqxfile

COLUMNS = ["magic", "strategy", "identity", "sqx", "firm", "since"]
TIMEFRAMES = {"M1", "M5", "M15", "M30", "H1", "H4", "D1"}


def read(path: Path) -> pd.DataFrame:
    """The register, refused when absent or ambiguous — it is the owner's file, never guessed.

    Args:
        path: CSV with COLUMNS: the EA's magic number, the strategy's name, its identity
            (`core.sqxfile.identity`), its `.sqx`, the firm key of `mt5_accounts` it runs
            on, and the day it went live (YYYY-MM-DD).

    Returns:
        One row per live EA, `since` as a Timestamp. A magic used twice on one firm stops
        here: its deals could not be told apart.
    """
    if not path.exists():
        raise SystemExit(
            f"falta el registro de estrategias en real: {path}\n"
            f"Es un CSV con las columnas {','.join(COLUMNS)} — una fila por EA en real: su "
            "magic number, el nombre de la estrategia, su identidad, la ruta de su .sqx, la "
            "empresa (clave de mt5_accounts) y el día que empezó. Lo escribe el dueño; no se "
            "adivina por los nombres."
        )
    rows = pd.read_csv(
        path, dtype={"magic": int, "identity": str}, parse_dates=["since"]
    )
    missing = [c for c in COLUMNS if c not in rows.columns]
    if missing:
        raise SystemExit(f"{path.name}: faltan las columnas {', '.join(missing)}")
    twice = rows[rows.duplicated(["firm", "magic"], keep=False)]
    if len(twice):
        raise SystemExit(
            f"{path.name}: magic repetido en la misma empresa — "
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
