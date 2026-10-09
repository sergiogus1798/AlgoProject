"""One mother's batch through step 17's three compositions: values, filters, numbers and the call."""

import numpy as np
import pandas as pd

from core import assetdata
from engines.variants import filters, panel
from engines.weekly import flip, panel as weekly
from studies.optimisation.wfc.inputs import batch
from studies.optimisation.wfc.measure import level, order, reading
from studies.optimisation.wfc.verdict import state

STEP = 17
OOS2 = ("oos2",)
IDLE = "la madre no tiene operaciones en la ventana de fuera"
FEW = "quedan {n} variantes tras los filtros, menos de {need}"
STRADDLE = ("el {share:.0%} de las operaciones de fuera cierra en lunes o martes tras pasar el "
            "fin de semana abiertas: el nulo semanal puede salir estrecho. Con bloques de "
            "{weeks} semanas el orden sale «{order}»: la clasificación {change}")
GAP = ("el neto reconstruido no reproduce el NetProfit de SQX en el {share:.1%} de las "
       "variantes (el peor tramo)")


def values(comp: tuple[tuple, tuple], metrics: pd.DataFrame, got: dict,
           asset: dict) -> pd.DataFrame:
    """Each variant's excess per year on the two sides of one composition, net and gross.

    Args:
        comp: One of `panel.COMPOSITIONS`.
        metrics: Contract C3.
        got: What `inputs.batch.read` returned.
        asset: `assetdata.load` of the batch's asset.

    Returns:
        Indexed by `variant_id`: `e_is`, `e_oos` (net of costs) and `g_is`, `g_oos` (before
        them). A variant SQX returned with no trade on a side has an excess of zero there;
        one with trades counted and none exported stays NaN, and the filters drop it as
        `sin_valor`.
    """
    cols, counted = panel.columns(comp), metrics.set_index("variant_id")
    sides = {}
    for side, legs in (("is", comp[0]), ("oos", comp[1])):
        per = pd.concat([got["per"][leg] for leg in legs])
        total = (per.groupby("variant_id")[["net", "gross"]].sum()
                 / batch.years(asset, legs)).reindex(counted.index)
        idle = (counted[cols[f"trades_{side}"]] == 0).to_numpy()[:, None]
        total = total.mask(total.isna() & idle, 0.0)
        sides |= {f"e_{side}": total["net"], f"g_{side}": total["gross"]}
    return pd.DataFrame(sides)


def composition(comp: tuple[tuple, tuple], metrics: pd.DataFrame, got: dict, symbol: str,
                k: int, cfg: dict, deciding: bool, name: str = "") -> dict:
    """One composition, from the batch to its facts.

    Args:
        comp: One of `panel.COMPOSITIONS`.
        metrics: Contract C3.
        got: What `inputs.batch.read` returned.
        symbol: The asset.
        k: Parameters that move in the batch (`inputs.batch.live`).
        cfg: The study's config.
        deciding: Whether this composition's state is the step's.
        name: The mother's batch name, kept in the recorded draws.

    Returns:
        `facts` (numbers, plus the words `orden` and, when deciding, `estado`), `kept` (the
        measured variants: `variant_id`, `stratum`, net `e_is` and `e_oos`, `top`) and
        `notes`, and `draws` (`core.study.draws` rows; absent when nothing was measured). Raises
        PermissionError from the seal before any out-of-sample column is read.
    """
    asset, cols = assetdata.load(symbol), panel.columns(comp)
    span, e = batch.years(asset, comp[1]), values(comp, metrics, got, asset)

    def screen(floors: bool) -> tuple[pd.DataFrame, dict]:
        """The variants measured, exact duplicates told by their trade lists."""
        return filters.screen(metrics, comp, k, span, symbol, e, floors=floors, step=STEP,
                              cfg=cfg["panel"], prints=got["prints"])

    kept, counts = screen(True)
    notes, need = counts.pop("avisos"), cfg["panel"]["min_variants"]
    facts = {key: v for key, v in counts.items() if key != "sin_dato"} | {"vivos": k}
    mother = metrics.loc[metrics["stratum"] == filters.ORIGIN, cols["trades_oos"]]
    if mother.iloc[0] == 0 or len(kept) < need:
        notes.append(IDLE if mother.iloc[0] == 0 else FEW.format(n=len(kept), need=need))
        facts |= {"n": len(kept), "orden": state.NO_DATA}
        if deciding:
            facts["estado"] = state.state(state.NO_DATA, np.nan, len(kept), need, np.nan, np.nan)
        return {"facts": facts, "kept": kept.assign(top=False), "notes": notes}
    ids = kept["variant_id"]
    per = pd.concat([got["per"][leg] for leg in comp[1]])
    per = per[per["variant_id"].isin(ids)]
    weeks = weekly.weekly(per, batch.window(asset, comp[1]), units=ids)
    inside = {"net": kept["e_is"].to_numpy(float), "gross": e.loc[ids, "g_is"].to_numpy(float)}
    outside = {"net": kept["e_oos"].to_numpy(float), "gross": e.loc[ids, "g_oos"].to_numpy(float)}
    rows = []
    found = reading.measure(inside, outside, {name: w.to_numpy() for name, w in weeks.items()},
                            span, cfg, weekly.straddle(per["open"], per["close"]), name,
                            panel.label(comp), rows)
    said = state.judge(found, cfg)
    best = level.top(inside["net"], cfg["level"]["top_share"])
    facts |= found | {key: word for key, word in said.items() if key != "estado"}
    if "orden_bloque" in said:
        notes.append(STRADDLE.format(
            share=found["fines_de_semana"], weeks=cfg["annotate"]["block_weeks"],
            order=said["orden_bloque"],
            change="cambia" if said["orden_bloque"] != said["orden"] else "no cambia"))
    counted = metrics.set_index("variant_id").loc[ids, [cols["trades_is"], cols["trades_oos"]]]
    facts["rho_parcial"] = order.partial(inside["gross"], outside["gross"],
                                         counted.to_numpy(float))
    if comp[1] == OOS2:
        prior = got["prior"].reindex(ids).fillna(0.0).to_numpy() / span
        facts["nivel_top_deriva_previa"] = float(np.median(prior[best]))
    if deciding:
        loose = e.loc[screen(False)[0]["variant_id"]]
        facts |= {"estado": said["estado"], "n_sin_suelos": len(loose),
                  "rho_sin_suelos": float(flip.spearman(loose["g_is"].to_numpy(float),
                                                        loose["g_oos"].to_numpy(float)))}
    return {"facts": facts, "kept": kept.assign(top=best), "notes": notes,
            "draws": rows}


def run(metrics: pd.DataFrame, got: dict, symbol: str, cfg: dict,
        name: str = "") -> dict[str, dict]:
    """The three compositions of one batch, and whether the trades add up to SQX's figures.

    Args:
        metrics: Contract C3: the batch's `metrics.parquet`.
        got: What `inputs.batch.read` returned.
        symbol: The asset.
        cfg: The study's config.
        name: The mother's batch name, kept in the recorded draws.

    Returns:
        `c1`, `c2`, `c3` -> what composition() returned, each with the fact `descuadre_sqx`:
        the largest share, over the legs, of variants whose repriced net profit misses SQX's
        `NetProfit` by more than `check`'s tolerance. Above zero, the deciding one says so.
    """
    k, check = batch.live(metrics, filters.CONTROLS), cfg["check"]
    measured = {key: composition(comp, metrics, got, symbol, k, cfg,
                                 panel.label(comp) == cfg["deciding"], name)
                for key, comp in panel.KEYS.items()}        # the seal is asked in here
    sqx = metrics.set_index("variant_id")
    off = max(weekly.sqx_gap(per, sqx[f"NetProfit ({leg})"], tolerance=check["sqx_tolerance"],
                             relative=check["sqx_relative"])[0]
              for leg, per in got["per"].items())
    for got_one in measured.values():
        got_one["facts"]["descuadre_sqx"] = float(off)
        if "estado" in got_one["facts"] and off > 0:
            got_one["notes"].append(GAP.format(share=off))
    return measured
