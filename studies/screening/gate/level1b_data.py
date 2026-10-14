"""Level 1b of the gate: what the edge keeps without the trades that touch a feed anomaly."""

import json
import logging
from pathlib import Path
from typing import cast

import pandas as pd

from studies.screening.analysis import dataquality

FACTS = dataquality.FACTS
log = logging.getLogger(__name__)


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Data-quality facts for the strategies alive.

    Args:
        data: The harvest as `inputs.load` gives it, plus `oos` (level 1a's per-trade table), `bars`
            and `quality`, the feed's `feedQuality` folder (`core.paths.feed_quality_dir`; package I
            puts it there, or leaves it out when the feed has none).
        alive: Identities still in the cascade.
        cfg: The gate's config (unused).

    Returns:
        One row per identity, one column per fact of `FACTS`. All NaN (-> Limbo at the judge, with
        the reason logged) when the feed has no inventory or it ends before the population's last
        trade; `ret_datos` is NaN when the mean excess is not positive.
    """
    empty = pd.DataFrame(index=alive, columns=pd.Index(FACTS), dtype=float)
    if not data:       # tests/test_gate_rules.py runs every level on an empty harvest
        return empty
    folder = cast(Path, data.get("quality"))     # absent -> TypeError below, caught: no inventory
    try:
        ev = pd.read_parquet(folder / "events.parquet")
        scanned_to = pd.Timestamp(json.loads((folder / "summary.json").read_text("utf-8"))["bars_to"])
    except (TypeError, OSError, KeyError, ValueError) as err:
        log.warning("calidad de datos: sin inventario utilizable (%s: %s); hechos ausentes",
                    type(err).__name__, err)
        return empty
    oos, index = data["oos"], data["bars"].index
    if scanned_to < oos["close_time"].max():
        log.warning("calidad de datos: el inventario acaba en %s, antes de la ultima operacion (%s); "
                    "hechos ausentes", scanned_to, oos["close_time"].max())
        return empty
    width = int(cast(pd.Timedelta, pd.Series(index[:1000]).diff().mode()[0]).total_seconds() // 60)
    return dataquality.facts(oos, dataquality.mark(oos, index, width, ev)).reindex(alive)
