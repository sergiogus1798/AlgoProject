"""One variant batch through step 18.5: the common sets, the readings, the reference and the facts."""

from typing import Any, cast
import numpy as np
import pandas as pd

from engines.variants import fingerprint
from engines.weekly import flip
from studies.optimisation.marketSurfaces.inputs import batch
from studies.optimisation.marketSurfaces.measure import premium, reading
from studies.optimisation.marketSurfaces.verdict import call

MAIN = batch.MAIN
INSIDE = (
    "build",
    "oos1",
)  # the main market's window in every reading, and the others' in the deciding one
OOS2 = ("oos2",)  # the others' window in the oos2 reading


def legs(feeds: list[str], oos2: bool) -> dict[str, tuple]:
    """Which legs are read on which market: the main one never needs oos2."""
    return {MAIN: INSIDE} | {feed: INSIDE + OOS2 * oos2 for feed in feeds}


def measure(
    data: dict,
    design: batch.Design,
    table: pd.DataFrame,
    years: dict,
    cfg: dict,
    oos2: bool,
) -> dict[str, Any]:
    """Every number of one batch, nothing judged.

    Args:
        data: Market -> what `inputs.batch.one` returned, `Main` and every feed of `table`.
        design: `inputs.batch.variants`: `ids`, `mother`, `k`.
        table: `inputs.markets.declared` of the asset.
        years: Market -> leg -> the length of that leg there, in years.
        cfg: The study's config.
        oos2: Whether the oos2 reading is measured; False touches no oos2 key of `data`.

    Returns:
        `principal` (the deciding reading, `measure.reading.measure`), `oos2` (the same on
        the others' oos2, None when not asked), `dos_semanas` (the deciding order again with
        two-week blocks, None unless `straddle` exceeds `null.straddle_max`), `auto` (the
        main market's build against its oos1), `usable` and `duplicados` (variants usable on
        the main market, share dropped as exact duplicates there), `straddle`, `gaps`
        (market -> worst share of variants off SQX's NetProfit) and `totals` (market -> each
        variant's gross excess over the deciding window, `Main` included) with `ok` (market ->
        its common set).
    """
    ids, main, floors = design["ids"], data[MAIN]["legs"], cfg["panel"]
    traded = sum(main[leg]["n"] for leg in INSIDE)
    kept, duplicates = fingerprint.keep(data[MAIN]["prints"], first=[design["mother"]])
    usable = (
        pd.Index(ids).isin(kept)
        & (
            traded
            >= floors["floor_oos_per_year"] * sum(years[MAIN][leg] for leg in INSIDE)
        )
        & (traded >= floors["floor_is_per_param"] * design["k"])
    )
    gross = {leg: main[leg]["gross"].to_numpy().sum(axis=0) for leg in INSIDE}
    x = gross["build"] + gross["oos1"]
    net = cast(
        np.ndarray, sum(main[leg]["net"].to_numpy().sum(axis=0) for leg in INSIDE)
    )
    best = (
        premium.top(net, usable, cfg["premium"]["top_share"])
        if usable.any()
        else np.zeros(len(ids), bool)
    )
    mother = ids.index(design["mother"])
    seeds = np.random.SeedSequence(cfg["null"]["seed"]).spawn(3)

    def markets(window: tuple) -> dict[str, Any]:
        """Each feed's panels over one window and its common set with the main market."""
        out = {}
        for feed in table["feed"]:
            got = [data[feed]["legs"][leg] for leg in window]
            n = sum(leg["n"] for leg in got)
            need = floors["floor_oos_per_year"] * sum(
                years[feed][leg] for leg in window
            )
            out[feed] = {
                "gross": batch.stacked(got, "gross"),
                "net": batch.stacked(got, "net"),
                "ok": usable & (n >= need) & (n > 0),
            }
        return out

    inside = markets(INSIDE)
    found = reading.measure(x, best, inside, table, mother, cfg, seeds[0])
    read = [data[feed]["legs"][leg] for feed in table["feed"] for leg in INSIDE]
    trades = sum(leg["trades"] for leg in read)
    straddle = (
        sum(leg["straddle"] * leg["trades"] for leg in read) / trades if trades else 0.0
    )
    wide = (
        reading.measure(
            x, best, inside, table, mother, cfg, seeds[2], block_weeks=2, planted=False
        )
        if straddle > cfg["null"]["straddle_max"]
        else None
    )
    return {
        "principal": found,
        "dos_semanas": wide,
        "straddle": float(straddle),
        "oos2": reading.measure(
            x, best, markets(OOS2), table, mother, cfg, seeds[1], planted=False
        )
        if oos2
        else None,
        "auto": float(flip.spearman(gross["build"][usable], gross["oos1"][usable]))
        if usable.sum() > 2
        else float("nan"),
        "usable": int(usable.sum()),
        "duplicados": float(duplicates),
        "gaps": {
            m: max(gaps)
            for m, got in data.items()
            if (
                gaps := [
                    leg["gap"] for leg in got["legs"].values() if leg["gap"] is not None
                ]
            )
        },
        "totals": {MAIN: x}
        | {feed: got["gross"].sum(axis=0) for feed, got in inside.items()},
        "ok": {MAIN: usable} | {feed: got["ok"] for feed, got in inside.items()},
    }


def facts(measured: dict, cfg: dict) -> tuple[dict, str]:
    """What the judge and step 20 read, and the step's state.

    Args:
        measured: What measure() returned.
        cfg: The study's config.

    Returns:
        (the facts, `pass` / `watch` / `fail`). `orden.estado` is absent when the order has
        no data, `prima.bajo_p5` when the premium could not be measured, `auto.cociente`
        unless rho_auto exceeds `reference.min_rho`, `orden.estado_2sem` unless the two-week
        null was drawn, and the whole `oos2` block unless that reading was measured
        (`oos2.perverso` is absent when that reading had no data: `oos2.sin_dato = 1`).
    """
    alpha, floor = cfg["null"]["alpha"], cfg["markets"]["min_weight"]
    main, tail = (
        measured["principal"],
        ("rho", "p_mas", "p_menos", "nulo_p5", "nulo_p95"),
    )
    said, low = call.order(main["orden"], alpha, floor), main["prima"]["bajo"]
    out = {
        "orden": {k: main["orden"][k] for k in tail}
        | {
            "mercados": main["orden"]["peso"],
            "n_mercados": main["orden"]["mercados"],
            "finde": measured["straddle"],
        },
        "prima": {"valor": main["prima"]["valor"], "nulo_p5": main["prima"]["nulo_p"]},
        "auto": {"rho": measured["auto"]},
        "potencia": main["potencia"],
        "variantes": measured["usable"],
        "duplicados": measured["duplicados"],
        "costes": {"descuadre": max(measured["gaps"].values(), default=float("nan"))},
    }
    if said != call.NO_DATA:
        out["orden"]["estado"] = said
    if low is not None:
        out["prima"]["bajo_p5"] = int(low)
    if measured["auto"] > cfg["reference"]["min_rho"] and np.isfinite(
        main["orden"]["rho"]
    ):
        out["auto"]["cociente"] = main["orden"]["rho"] / measured["auto"]
    if measured["dos_semanas"]:
        again = call.order(measured["dos_semanas"]["orden"], alpha, floor)
        out["orden"] |= {"estado_2sem": again} if again != call.NO_DATA else {}
    later = None
    if measured["oos2"]:
        found = measured["oos2"]["orden"]
        later = call.order(found, alpha, floor)
        out["oos2"] = (
            {k: found[k] for k in tail[:3]}
            | {"mercados": found["peso"]}
            | (
                {"sin_dato": 1}
                if later == call.NO_DATA
                else {"sin_dato": 0, "perverso": int(later == "perverso")}
            )
        )
    return out, call.step(said, low, later)
