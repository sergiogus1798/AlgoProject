"""What the two routes read: one strategy's rows of the newest harvest, and its asset's bars cut at oos1."""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from core import assetdata, barstore
from core.paths import DATA
from ui.daemon.runs import context, guess_asset

SAMPLES = ("IS", "OOS")
NO_HARVEST = ("Este databank no tiene cosecha: la crea studies.screening.gate.harvest "
              "(skill /oos-gate).")


def newest(project: str, databank: str) -> Path | None:
    """The newest harvest day of one databank, by its folder date.

    Args:
        project: SQX project name.
        databank: Databank folder name.

    Returns:
        The harvest folder, or None when there is none.
    """
    days = sorted((DATA / "harvest" / project / databank).glob("*/metrics.parquet"))
    return days[-1].parent if days else None


def bad_name(*names: str) -> str | None:
    """Why a name typed into a query cannot be a folder of the data root, or None.

    Args:
        names: Project, databank or identity as the window sent them.

    Returns:
        The refusal sentence, or None.
    """
    wrong = [n for n in names if not n or "/" in n or "\\" in n or ".." in n]
    return f"Nombre no válido: «{wrong[0]}»." if wrong else None


def rows(harvest: Path, name: str, identity: str) -> pd.DataFrame:
    """One strategy's rows of one harvest parquet, read with a filter, never the whole file.

    Args:
        harvest: The harvest folder.
        name: "equity" or "trades".
        identity: The strategy's identity inside this databank.

    Returns:
        The rows of that identity.
    """
    return pq.read_table(harvest / f"{name}.parquet",
                         filters=[("identity", "==", identity)]).to_pandas()


def foreign_samples(frame: pd.DataFrame) -> str | None:
    """The refusal when a harvest holds a sample other than IS and OOS (the one-way door).

    Args:
        frame: Equity or trade rows with a `sample` column.

    Returns:
        The sentence, or None when every row is IS or OOS.
    """
    other = sorted(set(frame["sample"].astype(str)) - set(SAMPLES))
    return (f"La cosecha trae muestras {other} además de IS y OOS: la ventana no lee nada "
            "fuera de IS y OOS.") if other else None


def described(harvest: Path, identity: str) -> dict | None:
    """The strategy's name and timeframe, as SQX wrote them in `metrics.parquet`.

    Args:
        harvest: The harvest folder.
        identity: The strategy's identity.

    Returns:
        `{name, tf}` (tf from `TimeFrame [IS]`, e.g. "H1"), or None when the identity is not
        in the harvest.
    """
    m = pq.read_table(harvest / "metrics.parquet",
                      columns=["identity", "strategy", "TimeFrame [IS]"],
                      filters=[("identity", "==", identity)]).to_pandas()
    return {"name": str(m["strategy"].iloc[0]), "tf": str(m["TimeFrame [IS]"].iloc[0])} \
        if len(m) else None


def market(project: str, databank: str, asset: str) -> dict | str:
    """The asset, its feed and the last day the window may show, exactly as the run buttons find them.

    Args:
        project: SQX project name.
        databank: Databank folder name.
        asset: The owner's override, empty to read it off the project's name.

    Returns:
        `{asset, feed, end}` (end = last day of oos1, "YYYY-12-31"), or the refusal sentence.
    """
    asset = asset or guess_asset(project)
    if not asset:
        return (f"No sé qué activo opera «{project}»: su nombre no contiene ningún símbolo de "
                "assets/symbols/. Elige el activo a mano.")
    if asset not in assetdata.symbols():
        return f"No conozco el activo «{asset}»: no está en assets/symbols/."
    c = context(project, databank, "", asset)
    if c["feed"] not in barstore.library():
        return (f"No hay barras M1 del feed {c['feed']} en la biblioteca: las trae "
                "python3 -m sqx.export.sync_bars.")
    return {"asset": asset, "feed": c["feed"], "end": c["end"]}


def bars(feed: str, tf: str, end: str) -> pd.DataFrame:
    """The feed's bars at one timeframe, cut after the last day of oos1 so oos2 never leaves.

    Args:
        feed: SQX symbol.
        tf: A key of `barstore.RULE`.
        end: Last day of oos1, "YYYY-MM-DD".

    Returns:
        Open, High, Low, Close, Volume indexed by bar open time. `barstore.read` writes the
        resampled timeframe under `barsDerived/` the first time it is asked, by design.
    """
    frame = barstore.read(feed, tf)
    return frame[frame.index < pd.Timestamp(end) + pd.Timedelta(days=1)]
