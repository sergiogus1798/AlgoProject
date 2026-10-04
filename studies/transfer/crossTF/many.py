"""Every mother across timeframes, scaled and not, read as one result: what the window paints."""

import time
from pathlib import Path

import numpy as np
import pandas as pd

from core import tradestore
from core.study import blocks, output, result as envelope
from engines.nulls import inputs as nullinputs
from studies.transfer.crossTF import cells, equity, inputs, verdict

MODULE = "studies.transfer.crossTF"
STATE = {"survives": "pass", "inherited": "watch", "fails": "fail", "no_data": "none",
         "silent": "none", "unusable": "none"}
MEANS_ES = {
    "unusable": "lleva un bloque custom con una longitud sin verificar: no se pudo escalar",
    "silent": "la entrada no disparó en ese timeframe en oos1: no hay nada que juzgar",
    "no_data": "sin datos: menos de 30 operaciones en oos1, en la hermana o en su madre",
    "survives": "bate a su nulo en oos1 más allá de lo que explica el resultado de su madre",
    "inherited": "gana en oos1, pero no más de lo que predice el resultado de su madre",
    "fails": "pierde en oos1"}
# The word of each reading as the owner reads it (the raw ids stay in verdict.csv for /curate).
READING_ES = {"survives": "Sobrevive", "inherited": "Heredada", "fails": "Falla",
              "silent": "Silenciosa", "unusable": "No utilizable", "no_data": "Sin datos"}
# The three roles a cell's role column takes that are not one of the five readings above, and
# the sentence each earns in the reading menu and the glossary (feedback §5, "?" para Baseline,
# Control, Scale).
TERMS_ES = {
    "Baseline": "La madre corrida sin tocar, en su propio timeframe (bloque 0 del retest): el "
                "número contra el que se compara todo lo demás.",
    "Control": "La hermana escalada, devuelta a jugar en el timeframe DE LA MADRE: lo que "
               "costó cambiar los parámetros por sí solo. Se enseña y no se juzga (propuesta "
               "de 2026-10-02): con periodos ÷4 es otra estrategia, no un control.",
    "Sin escalar (unscaled)": "La madre con sus periodos intactos, corrida en un timeframe más "
                              "lento. No se juzga: pregunta si el mercado se parece a sí mismo "
                              "a esa escala, no si la estrategia está sobreajustada.",
    "Escala (scaled)": "La hermana cuyos periodos y salidas por número de barras se reescalaron "
                       "a un timeframe más lento (sqx.variants.scale). El stop en precio no se "
                       "toca, así que en H4 es aproximadamente el doble de ancho en precio que "
                       "en H1 — una propiedad declarada de la comparación, no un error."}
# The selector's statistics: "Sharpe total" (`cells.TOTAL`, owner 2026-10-01) replaces the
# per-trade "sharpe", which the verdict still reads (VERDICT_STAT names it in a sentence): the
# null draws carry no calendar, so the daily Sharpe has no null to be judged against.
STAT_LABELS = {"net": "Net Profit", cells.TOTAL: "Sharpe total", "pf": "Profit Factor",
               "retdd": "Retorno/Drawdown", "dd": "Drawdown"}
VERDICT_STAT = {"sharpe": "el Sharpe por operación"}
SHOWN = {"sharpe": cells.TOTAL}
SCOPE = {"escalado": "Escalado", "sin_escalar": "Sin escalar"}
CURVE_POINTS = 50


def load(export: Path, scaling: Path, feed: str, cfg: dict, strategy: str | None = None) -> dict:
    """What the study reads: the plan of cells, the trades, each timeframe's bars, identity.

    Args:
        export: trades.parquet from sqx/export/export_retest.py.
        scaling: scaling.parquet from sqx.variants.scale.
        feed: SQX symbol the cells were run on.
        cfg: What `inputs.config` returned.
        strategy: A single mother's name, to read this batch as if it held only that one
            (feedback 2026-09-30 §1/§5: "Run solo esta estrategia"). None reads every mother.

    Returns:
        {"plan", "trades", "frames", "scaling", "nullcfg", "feed", "identity"}.
    """
    table = pd.read_parquet(scaling)
    if strategy:
        table = table[table["mother"] == strategy].reset_index(drop=True)
        if table.empty:
            raise SystemExit(f"{strategy!r} no es una madre de {scaling}: nada que fabricar")
    cfg["run"]["blocks"] = inputs.blocks(table, cfg["run"]["blocks"], scaling.parent)
    packed = inputs.oos(inputs.gather(scaling.parent, export, inputs.trades(export)), feed)
    plan = inputs.plan(table, cfg["run"]["blocks"])
    nullcfg = nullinputs.config(nullinputs.seeded(cfg["run"]["seed"]))
    # The null layer names whose costs its p-values carry, and the feed is the only thing
    # that says whose: a property of this run, not of the null machinery.
    nullcfg["feed"] = feed
    mothers = sorted(plan["mother"].unique())
    return {"plan": plan, "trades": packed, "scaling": table,
            "frames": inputs.bars(feed, cfg["run"]["blocks"]), "nullcfg": nullcfg,
            "feed": feed, "identity": output.identify(export.parent, mothers)}


def stat_grids(panel: pd.DataFrame, names: list[str]) -> list[dict]:
    """The mother-by-timeframe grid, one per statistic (feedback §5, "no solo Sharpe")."""
    out = []
    for name in names:
        wide = cells.matrix(panel, name)
        out.append({
            "kind": "grid", "title": "Lectura de todas las madres por timeframe",
            "rows": list(wide.index), "cols": [str(c) for c in wide.columns],
            "values": [[None if pd.isna(x) else float(x) for x in row] for row in wide.to_numpy()],
            "scale": "diverging", "levels": None, "labels": None,
            "select": {"statistic": STAT_LABELS.get(name, name)},
            "note": "Una celda vacía es real: una hermana escalada a H4 no tiene celda D1."})
    return out


def correlation_grid(plan: pd.DataFrame, packed: pd.DataFrame) -> dict | None:
    """The monthly-return correlation of every cell against its own mother's baseline."""
    corr = cells.correlations(plan, packed)
    if corr.empty:
        return None
    wide = corr.assign(cell=corr["role"] + "_" + corr["timeframe"]).pivot_table(
        index="mother", columns="cell", values="corr", observed=True)
    return {"kind": "grid", "title": "Correlación de los retornos mensuales contra la baseline, todas las madres",
           "rows": list(wide.index), "cols": [str(c) for c in wide.columns],
           "values": [[None if pd.isna(x) else float(x) for x in row] for row in wide.to_numpy()],
           "scale": "diverging", "levels": None, "labels": None,
           "help": "Correlación de Pearson entre el P/L MENSUAL de esta celda y el de la "
                   "baseline de la misma madre (los meses sin operar cuentan como 0, no se "
                   "descartan). Alta: la hermana gana y pierde en los mismos meses que la "
                   "madre — es la misma apuesta vista más despacio. Baja: aunque las dos ganen "
                   "dinero, no es el mismo negocio.",
           "note": "Sin celda cuando una de las dos partes no cubre al menos dos meses."}


def run(got: dict, cfg: dict) -> dict:
    """Every cell measured, every scaled cell read.

    Args:
        got: What load() returned.
        cfg: What `inputs.config` returned.

    Returns:
        {"population": the result, "panel": every cell, "table": one row per scaled
        sibling with its mother's identity and its reading as `verdict`, "nulls_seed": the
        root `engines.nulls.inputs.config` drew for this run's monkeys}.
    """
    started = time.time()
    envelope.progress(10, f"midiendo {len(got['plan'])} celdas contra sus nulos")
    panel = cells.panel(got["plan"], got["trades"], got["frames"], got["nullcfg"], cfg)
    readings = verdict.read(panel, got["scaling"], cfg)
    v = cfg["verdict"]
    pairs = ", ".join(f"bloque {i} = {tf}" for i, tf in enumerate(cfg["run"]["blocks"]))
    tfs = sorted(readings["timeframe"].unique())
    mothers = sorted(got["plan"]["mother"].unique())
    stat_names = [SHOWN.get(n, n) for n in got["nullcfg"]["statistics"]["report"]]
    judged = VERDICT_STAT.get(v["statistic"], STAT_LABELS.get(v["statistic"], v["statistic"]))
    scaled_table = readings.drop(columns=["warnings"]).assign(
        significa=readings["reading"].map(MEANS_ES))
    unscaled_table = verdict.unscaled(panel)
    table = readings.drop(columns=["warnings"]).assign(
        strategy=readings["mother"], identity=readings["mother"].map(got["identity"]),
        verdict=readings["reading"])

    null_note = (f"Las {len(panel)} celdas —baseline, control, escaladas y sin escalar— se "
                f"miden todas contra EL MISMO nulo: `{v['rung']}` (aleatoriza únicamente en "
                f"qué vela entra cada operación; cuántas veces y cuánto se arriesga se dejan "
                f"fijos), sobre {judged} y SOLO en oos1. Lo único "
                f"que cambia celda a celda es sobre qué barras se dibuja ese nulo: las de su "
                f"propio timeframe. Bloques de resultado leídos como {pairs}.")
    def scaled_one(rows: pd.DataFrame) -> dict:
        """The scaled siblings' table of one mother."""
        tbl = blocks.table("Cada hermana escalada, juzgada", rows)
        tbl["select"] = {"scope": SCOPE["escalado"]}
        tbl["help"] = [None, None, None, None, None, None, None,
                       TERMS_ES["Baseline"], TERMS_ES["Control"], None, None]
        return tbl

    def unscaled_one(rows: pd.DataFrame) -> dict:
        """The unscaled table of one mother."""
        tbl = blocks.table("La madre en cada timeframe, sin escalar", rows,
                           "Sin veredicto: pregunta si el mercado es autosimilar a esa "
                           "escala, no si la estrategia está sobreajustada. Fallar aquí no "
                           "dice nada de ella.")
        tbl["select"] = {"scope": SCOPE["sin_escalar"]}
        return tbl

    reading_menu = {"kind": "list", "title": "Qué significa cada lectura",
                    "note": "En el orden en que se comprueban. Las tres primeras dicen que la "
                            "prueba no se pudo hacer (limbo), no que la estrategia falle. "
                            "La z nueva (z_new) es lo que la hermana añade a lo que ya "
                            "enseñó su madre.",
                    "items": [{"title": k.capitalize(), "text": t}
                             for k, t in MEANS_ES.items()]
                             + [{"title": k, "text": t} for k, t in TERMS_ES.items()]}
    corr = correlation_grid(got["plan"], got["trades"])
    body = ([{"kind": "callout", "state": "info", "text": null_note}]
           + equity.blocks(got["plan"], got["trades"])
           + stat_grids(panel, stat_names)
           + ([corr] if corr else [])
           + [{"kind": "bars", "title": "Cómo cayó la población (todas las madres)", "unit": "hermanas",
               "reference": None,
               "items": [{"label": f"{tf} · {READING_ES[r]}", "value": int(n), "error": None,
                         "state": STATE[r]} for tf, tally in verdict.counts(readings).items()
                        for r, n in sorted(tally.items())]},
              reading_menu] + equity.per_mother(scaled_one, scaled_table, mothers)
           + equity.per_mother(unscaled_one, unscaled_table, mothers))
    tabs = [envelope.tab("crossTF", "Resultado por timeframe", body, selectors=[
        {"key": "mother", "label": "Madre", "options": mothers, "default": mothers[0]},
        {"key": "statistic", "label": "Estadístico", "help": "El estadístico que dibuja el "
         "mapa de calor. No mueve el veredicto, que se lee siempre sobre "
         f"{judged} contra su nulo. Sharpe total: "
         "P&L de cada día hábil del backtest de la celda (los días sin cierres cuentan como "
         "0), media / desv. × √252.",
         "options": [STAT_LABELS.get(n, n) for n in stat_names],
         "default": STAT_LABELS.get(SHOWN.get(v["statistic"], v["statistic"]), v["statistic"])},
        {"key": "scope", "label": "Ámbito", "help": "Escalado: la pregunta de robustez, con "
         "veredicto. Sin escalar: si el mercado es autosimilar a esa escala, sin veredicto.",
         "options": list(SCOPE.values()), "default": SCOPE["escalado"]}])]
    warn = [{"code": f"{r.mother}:{r.timeframe}", "state": "watch", "text": w}
            for r in readings.itertuples() for w in r.warnings]
    counts = readings["reading"].value_counts()
    said = blocks.verdict(
        f"{int(counts.get('survives', 0))} de {len(readings)} sobreviven",
        "pass" if counts.get("survives", 0) else "fail",
        "Una hermana escalada sobrevive si bate al nulo de timing de su timeframe en oos1 más "
        "allá de lo que explica su madre. " + " ".join(f"{tf}: " + ", ".join(
            f"{READING_ES[r].lower()} {n}" for r, n in sorted(t.items())) + "." for tf, t in
                                      verdict.counts(readings).items()))
    glossary = [{"term": k, "text": t} for k, t in MEANS_ES.items()] \
        + [{"term": k, "text": t} for k, t in TERMS_ES.items()]
    population = envelope.envelope(MODULE, None, None, cfg, started, tabs, said, warn, glossary)
    envelope.progress(100, f"{len(readings)} hermanas en {len(tfs)} timeframes")
    return {"population": population, "panel": panel, "table": table,
            "nulls_seed": got["nullcfg"]["nulls"]["seed"]}
