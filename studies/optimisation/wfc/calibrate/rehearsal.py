"""The criterion rehearsed on real batches with build inside and oos1 outside: legs already spent."""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from core import assetdata
from engines.variants import filters, look
from engines.weekly import panel as weekly
from studies.optimisation.wfc import one
from studies.optimisation.wfc.calibrate import rates
from studies.optimisation.wfc.inputs import batch
from studies.optimisation.wfc.verdict import state

LEGS = ("build", "oos1")
COMP = (("build",), ("oos1",))
SEALED = "oos2"


def batches(root: Path) -> list[Path]:
    """The batch folders under `root` (<project>/<strategy>/) that hold every variant's trades."""
    return sorted(found.parent for found in root.glob(f"*/*/{batch.TRADES}"))


def metrics(work: Path) -> pd.DataFrame:
    """The batch's contract C3 without opening a column of oos2.

    Exact duplicates are told by the trades of the legs read, so here a duplicate is one
    whose trade list matches in build and oos1.
    """
    file = work / "metrics.parquet"
    names = [name for name in pq.read_schema(file).names if SEALED not in name]
    return pd.read_parquet(file, columns=names)


def one_batch(work: Path, cfg: dict) -> dict:
    """One batch through the criterion, both ways.

    Args:
        work: A folder of batches().
        cfg: The WFC's config.

    Returns:
        `lote`, `n`, `casilla`, `estado` (the criterion), `estado_sin` (without a null on
        the level), and when it was measured `rho`, `nivel_top`, `p_nivel` and `sd_rho_nulo`
        (None otherwise).
    """
    symbol, timeframe = look.market(work)
    table = metrics(work)
    got = batch.read(work, symbol, timeframe, LEGS)
    out = one.composition(COMP, table, got, symbol, batch.live(table, filters.CONTROLS), cfg, True)
    facts, kept = out["facts"], out["kept"]
    row = {"lote": f"{work.parent.name}/{work.name}", "n": facts["n"], "estado": facts["estado"],
           "casilla": state.NO_DATA, "estado_sin": "limbo", "rho": None, "nivel_top": None,
           "p_nivel": None, "sd_rho_nulo": None}
    if facts["orden"] == state.NO_DATA:
        return row
    asset, ids = assetdata.load(symbol), kept["variant_id"]
    per = got["per"][LEGS[1]]
    weeks = weekly.weekly(per[per["variant_id"].isin(ids)], batch.window(asset, COMP[1]),
                          units=ids)["gross"].to_numpy()
    inside = one.values(COMP, table, got, asset).loc[ids, "g_is"].to_numpy(float)
    return row | {
        "casilla": rates.cell(facts["orden"], facts["nivel_top"]), "rho": facts["rho"],
        "nivel_top": facts["nivel_top"], "p_nivel": facts["p_nivel"],
        "estado_sin": rates.without_level_null(facts["orden"], facts, cfg),
        "sd_rho_nulo": rates.sd_rho(inside, weeks, batch.years(asset, COMP[1]), cfg)}


def run(root: Path, cfg: dict) -> dict:
    """Every batch under `root` that can be rehearsed.

    Returns:
        `lotes`: one row of one_batch() each; `tasas`: `rates.shares` over them, None when
        there is no batch. The truth of a real batch is not known: these are the rates of
        each cell, never a false or a missed PASA.
    """
    rows = [one_batch(work, cfg) for work in batches(root)]
    return {"lotes": rows, "tasas": rates.shares(rows) if rows else None}
