"""One variant batch read as one surface per market, compared pair by pair, as the contract's data."""

import time
from pathlib import Path

import numpy as np
import pandas as pd

from core import assetdata
from core.study import blocks, result as envelope
from studies.optimisation.marketSurfaces.contract import tabs
from studies.optimisation.marketSurfaces.inputs import surfaces
from studies.optimisation.marketSurfaces.measure import pairs, verify
from studies.optimisation.marketSurfaces.verdict import call

MODULE = "studies.optimisation.marketSurfaces"
ORIGIN = "P00000"


def origin_pct(cells: pd.DataFrame) -> pd.DataFrame:
    """Where the mother sits in each market's surface.

    Args:
        cells: `inputs.surfaces.long`, usable cells only.

    Returns:
        One row per (market, segment): the share of variants that did worse than the
        mother, in per cent. 100 means the mother is that market's best tuple.
    """
    rows = []
    for (market, segment), g in cells.groupby(["market", "segment"]):
        mine = g.loc[g["variant_id"] == ORIGIN, "value"]
        pct = 100 * float((g["value"] < mine.iloc[0]).mean()) if len(mine) else float("nan")
        rows.append({"market": market, "segment": segment, "origin_pct": pct})
    return pd.DataFrame(rows)


def measure(work: Path, cfg: dict, symbol: str) -> dict:
    """Every number of one batch, nothing judged and nothing written.

    Args:
        work: The batch directory: `segments.parquet`, `metrics.parquet`, `equity.parquet`,
            `equity_markets.parquet`.
        cfg: What `inputs.config.load` returned.
        symbol: The main asset, whose `_markets.yaml` block fixes the markets.

    Returns:
        The cells, the pairs of every segment, the main-against-each rows, the checks, the
        declared and absent markets and the cost flag of each.
    """
    feed, timeframe = surfaces.main_feed(work)
    declared = surfaces.declared(symbol)
    cells = surfaces.long(work, cfg["segments"], cfg["metric"], cfg["min_trades"], feed)
    absent = [m for m in declared if m not in set(cells["market"])]
    order = [feed] + [m for m in declared if m not in absent]
    envelope.progress(30, f"{cells['variant_id'].nunique()} variantes x {len(order)} mercados")

    found = pd.concat([pairs.matrix(surfaces.wide(cells, s, order),
                                    surfaces.wide(cells, s, order, "exposure"),
                                    cfg["top_share"], cfg["j_quantile"]).assign(segment=s)
                       for s in cfg["segments"]], ignore_index=True)
    rows = call.against_main(found, feed, cfg["rho_floor"]).merge(
        origin_pct(cells[cells["usable"]]), on=["market", "segment"])
    envelope.progress(55, "pares medidos; verificando contra las curvas diarias")

    lo, hi = assetdata.window(assetdata.load(symbol), "build")
    build = (pd.Timestamp(lo, unit="ms"), pd.Timestamp(hi, unit="ms") - pd.Timedelta(days=1))
    checked = pd.concat([verify.main(work, cells, feed, build),
                         verify.markets(work, cells, order[1:])], ignore_index=True)
    envelope.progress(90, "verificado")
    return {"feed": feed, "timeframe": timeframe, "declared": declared, "absent": absent,
            "order": order, "cells": cells, "pairs": found, "rows": rows, "checks": checked,
            "diagonal": verify.diagonal(found),
            "provisional": {m: surfaces.provisional(m) for m in [feed] + declared}}


def warnings(m: dict) -> list[dict]:
    """What colours the result without removing anything from it."""
    out = []
    costly = [tabs.short(k) for k, v in m["provisional"].items() if v]
    if costly:
        out.append({"code": "costs_provisional", "state": "watch",
                    "text": f"{tabs.COSTS} Afecta a: {', '.join(costly)}."})
    if m["absent"]:
        out.append({"code": "market_absent", "state": "fail",
                    "text": f"Declarados en _markets.yaml y ausentes del lote: "
                            f"{', '.join(map(tabs.short, m['absent']))}. Cuentan como no "
                            f"superados; retestea el lote con ellos."})
    bad = m["checks"][m["checks"]["rho"] < verify.RANK_AGREES]
    diag = m["diagonal"][~np.isclose(m["diagonal"]["rho"], 1.0) | (m["diagonal"]["j"] != 1.0)]
    if len(bad) or len(diag):
        out.append({"code": "verification", "state": "fail",
                    "text": f"{len(bad)} comprobaciones de curva y {len(diag)} de diagonal "
                            f"fallan: la superficie puede no ser la del mercado que dice."})
    out.append({"code": "family_only", "state": "info",
                "text": "Los 9 mercados son de la misma familia macro que el principal "
                        "(_markets.yaml, sin structural): pasar aquí es la prueba fácil; "
                        "fallar sí dice algo."})
    return out


def result(m: dict, cfg: dict, started: float, strategy: str) -> dict:
    """The contract's result of what `measure` returned.

    Args:
        m: What `measure` returned.
        cfg: The config it ran under.
        started: time.time() at the start.
        strategy: The mother's name.

    Returns:
        The validated result dict, with the mother-level call as its verdict.
    """
    said = call.mother(m["rows"], len(m["declared"]), cfg["min_share"])
    parts = [{"label": f"{tabs.short(r.market)} {r.segment}", "state": r.state,
              "value": r.rho, "note": f"J {r.j:.2f} (azar {r.j0:.2f})"}
             for r in m["rows"].itertuples()]
    verdict = blocks.verdict(said["label"], said["state"],
                             said["meaning"] + " " + tabs.COSTS, None, parts)
    usable = m["cells"][m["cells"]["usable"]]
    return envelope.envelope(
        MODULE, strategy, None, cfg, started,
        [tabs.reading(m["rows"], cfg["segments"], cfg["rho_floor"]),
         tabs.matrices(m["pairs"], cfg["segments"], m["order"]),
         tabs.surfaces(usable, cfg["segments"], m["order"], ORIGIN),
         tabs.checks(m["checks"], m["diagonal"], verify.RANK_AGREES)],
        verdict, warnings(m),
        [{"term": "rho_ab", "text": "Spearman del beneficio neto entre las variantes de dos "
                                    "mercados: si ordenan igual las combinaciones."},
         {"term": "J_ab", "text": "Jaccard de los deciles superiores: qué parte de las mejores "
                                  "combinaciones son las mismas en los dos mercados."},
         {"term": "n_eff", "text": "Variantes con un resultado distinto en el par: dos tuplas "
                                   "que dan el mismo backtest cuentan una vez."}],
        {"call": said["label"], "state": said["state"], "passed": said["passed"],
         "declared": len(m["declared"]), "markets": len(m["order"]),
         "variants": int(m["cells"]["variant_id"].nunique()),
         "segments": cfg["segments"], "costs_provisional": any(m["provisional"].values())})


def run(strategy: str, work: Path, cfg: dict, symbol: str) -> dict:
    """One batch, measured and read — what the window calls.

    Args:
        strategy: The mother's name.
        work: The batch directory.
        cfg: What `inputs.config.load` returned.
        symbol: The main asset.

    Returns:
        The contract's result dict.
    """
    started = time.time()
    return result(measure(work, cfg, symbol), cfg, started, strategy)
