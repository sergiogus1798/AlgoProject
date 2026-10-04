"""One variant batch read as one surface per market, compared pair by pair, as the contract's data."""

import time
from pathlib import Path

import numpy as np
import pandas as pd

from core import assetdata
from core.study import blocks, result as envelope
from core.surface import dedupe
from studies.optimisation.marketSurfaces.contract import criteria, density, grids, tabs
from studies.optimisation.marketSurfaces.inputs import surfaces
from studies.optimisation.marketSurfaces.measure import lift, pairs, region, verify
from studies.optimisation.marketSurfaces.verdict import call

MODULE = "studies.optimisation.marketSurfaces"
ORIGIN = "P00000"
# How a config's metric column is named on screen and in which unit. Extend when `config.yaml`'s
# `metric`, `extra_metrics` or `density_metrics` takes another value.
METRIC_LABEL = {"NetProfit": "Net Profit", "ProfitFactor": "Profit Factor", "SharpeRatio": "Sharpe",
                "ReturnDDRatio": "Ret/DD", "SortinoRatio": "Sortino"}
UNIT = {"Net Profit": "USD"}


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


def lifts(work: Path, cells: pd.DataFrame, order: list[str], cfg: dict) -> dict:
    """The criteria metrics of every segment (`measure.lift`): computed, judged by nothing.

    Args:
        work: The batch directory.
        cells: `inputs.surfaces.long`.
        order: The main market first, then the declared ones present.
        cfg: What `inputs.config.load` returned.

    Returns:
        Segment → {"markets": market → `lift.market`, "all": `lift.together`}. A market
        that shares fewer than `lift.MIN_VARIANTS` distinct usable variants with the main
        one is left out: its numbers are missing, never zero. One sign per calendar day is
        drawn for every market at once, so the markets stay as correlated as they are.
    """
    out = {}
    for segment in cfg["segments"]:
        wide = surfaces.wide(cells, segment, order)
        panels = {m: surfaces.days(work, m, segment) for m in order[1:]}
        dates = sorted(set().union(*(p.index for p in panels.values())))
        signs = pd.DataFrame(np.random.default_rng(lift.SEED).choice(
            [-1.0, 1.0], size=(lift.DRAWS, len(dates))), columns=dates)
        found = {}
        for m, panel in panels.items():
            kept = dedupe.distinct(wide[[order[0], m]].dropna().set_axis(["a", "b"], axis=1),
                                   ("a", "b"))
            ids = list(kept.index)
            # No daily curve for these variants in this segment (the harvest kept none): the
            # null cannot be drawn, so the market's numbers are missing here too.
            if len(kept) < lift.MIN_VARIANTS or not set(ids) <= set(panel.columns):
                continue
            ta, tb = (pairs.top(kept[c], cfg["top_share"]) for c in ("a", "b"))
            null = lift.flipped(panel[ids].to_numpy(), signs[panel.index].to_numpy(), len(ta))
            found[m] = lift.market(kept.index.isin(ta), kept.index.isin(tb), null,
                                   ids.index(ORIGIN) if ORIGIN in ids else None)
        out[segment] = {"markets": found, "all": lift.together(found)}
    return out


def measure(work: Path, cfg: dict, symbol: str) -> dict:
    """Every number of one batch, nothing judged and nothing written.

    Args:
        work: The batch directory: `segments.parquet`, `metrics.parquet`, `equity.parquet`,
            `equity_markets.parquet`.
        cfg: What `inputs.config.load` returned.
        symbol: The main asset, whose `_markets.yaml` block fixes the markets.

    Returns:
        The cells, the variants' parameters, the pairs of every segment, the
        main-against-each rows, the checks, the declared and absent markets and the cost
        flag of each.
    """
    feed, timeframe = surfaces.main_feed(work)
    declared = surfaces.declared(symbol)
    cells = surfaces.long(work, cfg["segments"], cfg["metric"], cfg["min_trades"], feed)
    # The other metrics a heatmap or a density can show, precomputed so the window's selector
    # needs no second run (CONTRACT §1 «selectors», owner 2026-09-30 §8.5 and 2026-10-04 §19).
    by_metric = {METRIC_LABEL[k]: cells if k == cfg["metric"] else
                 surfaces.long(work, cfg["segments"], k, cfg["min_trades"], feed)
                 for k in [cfg["metric"], *cfg["extra_metrics"], *cfg["density_metrics"]]}
    absent = [m for m in declared if m not in set(cells["market"])]
    order = [feed] + [m for m in declared if m not in absent]
    envelope.progress(30, f"{cells['variant_id'].nunique()} variantes x {len(order)} mercados")
    # The plateau detected on the main asset (build segment), carried over to every market
    # as-is — never each market's own top share (owner, 2026-09-30 §8.5).
    params = surfaces.parameters(work)
    plateau = region.plateau(params, cells, ORIGIN, feed, cfg["region_radius"],
                             cfg["region_delta"])

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
    envelope.progress(80, "verificado; midiendo el Jaccard contra mercados sin ventaja")
    measured = lifts(work, cells, order, cfg)
    envelope.progress(90, "métricas para criterios medidas")
    return {"feed": feed, "timeframe": timeframe, "declared": declared, "absent": absent,
            "order": order, "cells": cells, "by_metric": by_metric, "params": params,
            "plateau": plateau, "pairs": found, "rows": rows, "checks": checked,
            "diagonal": verify.diagonal(found),
            "lifts": measured,
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
    why = grids.missing(m["params"], ORIGIN)
    if why:
        out.append({"code": "no_pair_grids", "state": "info", "text": why})
    elif not m["plateau"]:
        out.append({"code": "no_plateau", "state": "watch",
                    "text": "La madre no tiene celda con datos en el tramo build del mercado "
                            "principal: sin ella no hay meseta que trasladar, y el recuadro y "
                            "la tabla de dentro/fuera salen vacíos."})
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
              "value": r.rho, "shown": f"{r.rho:.2f}".replace(".", ","),
              "note": f"Jaccard {r.j:.2f} (por azar {r.j0:.2f})".replace(".", ",")}
             for r in m["rows"].itertuples()]
    verdict = blocks.verdict(said["label"], said["state"],
                             said["meaning"] + " " + tabs.COSTS, None, parts)
    usable = {k: c[c["usable"]] for k, c in m["by_metric"].items()}
    grid_metrics = list(usable)[:1 + len(cfg["extra_metrics"])]     # density-only ones stay out
    return envelope.envelope(
        MODULE, strategy, None, cfg, started,
        [criteria.into(tabs.reading(m["rows"], cfg["segments"], cfg["rho_floor"]), m["lifts"]),
         tabs.matrices(m["pairs"], cfg["segments"], m["order"]),
         density.tab(usable, {k: UNIT.get(k, "") for k in usable}, cfg["segments"], m["order"],
                     ORIGIN),
         *([] if grids.missing(m["params"], ORIGIN) else
           grids.tabs({k: usable[k] for k in grid_metrics}, m["params"], cfg["segments"],
                      m["order"], ORIGIN, cfg["top_share"], m["plateau"], cfg["region_radius"],
                      cfg["region_delta"])),
         tabs.checks(m["checks"], m["diagonal"], verify.RANK_AGREES)],
        verdict, warnings(m),
        [{"term": "Spearman (ρ)", "text": tabs.TERMS["Spearman"]},
         {"term": "Jaccard", "text": tabs.TERMS["Jaccard"]},
         {"term": "n efectivo", "text": tabs.TERMS["n_eff"]},
         {"term": "meseta del principal", "text": "Las variantes a pocos escalones de la "
          "madre en todos los parámetros a la vez, y no muy por debajo de su resultado en "
          "el mercado principal. Se calcula una sola vez ahí y se traslada tal cual a los "
          "demás mercados — no es el top propio de cada uno (eso es el mapa de consenso)."}],
        {"call": said["label"], "state": said["state"], "passed": said["passed"],
         "declared": len(m["declared"]), "markets": len(m["order"]),
         "variants": int(m["cells"]["variant_id"].nunique()),
         "segments": cfg["segments"], "costs_provisional": any(m["provisional"].values()),
         **criteria.summary(m["lifts"])})


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
