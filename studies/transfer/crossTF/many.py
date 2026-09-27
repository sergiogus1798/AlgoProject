"""Every mother across timeframes, scaled and not, read as one result: what the window paints."""

import time
from pathlib import Path

import pandas as pd

from core.study import blocks, output, result as envelope
from engines.nulls import inputs as nullinputs
from studies.transfer.crossTF import cells, inputs, verdict

MODULE = "studies.transfer.crossTF"
STATE = {"survives": "pass", "inherited": "watch", "fails": "fail", "control_failed": "watch",
         "silent": "none", "unusable": "none"}
MEANS_ES = {
    "unusable": "el redondeo o el recorte movió los parámetros demasiado para atribuir nada",
    "silent": "la entrada no disparó en ese timeframe: no hay nada que juzgar",
    "control_failed": "el cambio de parámetros solo ya la rompió en su propio timeframe",
    "survives": "bate al nulo de timing de su propio timeframe",
    "inherited": "gana en el timeframe nuevo, pero no se distingue del azar ahí",
    "fails": "no se traslada"}


def load(export: Path, scaling: Path, feed: str, cfg: dict) -> dict:
    """What the study reads: the plan of cells, the trades, each timeframe's bars, identity.

    Args:
        export: trades.parquet from sqx/export/export_retest.py.
        scaling: scaling.parquet from sqx.variants.scale.
        feed: SQX symbol the cells were run on.
        cfg: What `inputs.config` returned.

    Returns:
        {"plan", "trades", "frames", "scaling", "nullcfg", "feed", "identity"}.
    """
    table = pd.read_parquet(scaling)
    cfg["run"]["blocks"] = inputs.blocks(table, cfg["run"]["blocks"])
    plan = inputs.plan(table, cfg["run"]["blocks"])
    nullcfg = nullinputs.config([])
    # The null layer names whose costs its p-values carry, and the feed is the only thing
    # that says whose: a property of this run, not of the null machinery.
    nullcfg["feed"] = feed
    mothers = sorted(plan["mother"].unique())
    return {"plan": plan, "trades": inputs.trades(export), "scaling": table,
            "frames": inputs.bars(feed, cfg["run"]["blocks"]), "nullcfg": nullcfg,
            "feed": feed, "identity": output.identify(export.parent, mothers)}


def run(got: dict, cfg: dict) -> dict:
    """Every cell measured, every scaled cell read.

    Args:
        got: What load() returned.
        cfg: What `inputs.config` returned.

    Returns:
        {"population": the result, "panel": every cell, "table": one row per scaled
        sibling with its mother's identity and its reading as `verdict`}.
    """
    started = time.time()
    envelope.progress(10, f"midiendo {len(got['plan'])} celdas contra sus nulos")
    panel = cells.panel(got["plan"], got["trades"], got["frames"], got["nullcfg"], cfg)
    readings = verdict.read(panel, got["scaling"], cfg)
    v = cfg["verdict"]
    pairs = ", ".join(f"bloque {i} = {tf}" for i, tf in enumerate(cfg["run"]["blocks"]))
    wide = cells.matrix(panel, v["statistic"])
    tfs = sorted(readings["timeframe"].unique())
    table = readings.drop(columns=["warnings"]).assign(
        strategy=readings["mother"], identity=readings["mother"].map(got["identity"]),
        verdict=readings["reading"])
    tabs = [envelope.tab("scaled", "Las hermanas escaladas, juzgadas", [
        {"kind": "grid", "title": f"Lectura de cada madre por timeframe ({v['statistic']})",
         "rows": list(wide.index), "cols": [str(c) for c in wide.columns],
         "values": [[None if pd.isna(x) else float(x) for x in row] for row in wide.to_numpy()],
         "scale": "diverging", "levels": None, "labels": None,
         "note": "Una celda vacía es real: una hermana escalada a H4 no tiene celda D1."},
        {"kind": "bars", "title": "Cómo cayó la población", "unit": "hermanas",
         "reference": None,
         "items": [{"label": f"{tf} · {r}", "value": int(n), "error": None,
                    "state": STATE[r]} for tf, tally in verdict.counts(readings).items()
                   for r, n in sorted(tally.items())]},
        blocks.table("Cada hermana escalada", readings.drop(columns=["warnings"]).assign(
            significa=readings["reading"].map(MEANS_ES)))],
        note=f"Estadístico {v['statistic']} · nulo {v['rung']} · alpha {v['alpha']}. El "
             f"control se lee antes que la p: el orden de las comprobaciones es el orden de "
             f"la culpa. Bloques de resultado leídos como {pairs}."),
        envelope.tab("unscaled", "La madre en cada timeframe, sin escalar", [
            blocks.table("Madre sin tocar sus periodos", verdict.unscaled(panel))],
            note="Sin veredicto: pregunta si el mercado es autosimilar a esa escala, no si "
                 "la estrategia está sobreajustada. Fallar aquí no dice nada de ella.")]
    warn = [{"code": f"{r.mother}:{r.timeframe}", "state": "watch", "text": w}
            for r in readings.itertuples() for w in r.warnings]
    counts = readings["reading"].value_counts()
    said = blocks.verdict(
        f"{int(counts.get('survives', 0))} de {len(readings)} sobreviven",
        "pass" if counts.get("survives", 0) else "fail",
        "Una hermana escalada sobrevive si bate al nulo de timing de su propio timeframe con "
        "su control intacto. " + " ".join(f"{tf}: " + ", ".join(
            f"{r} {n}" for r, n in sorted(t.items())) + "." for tf, t in
                                      verdict.counts(readings).items()))
    population = envelope.envelope(MODULE, None, None, cfg, started, tabs, said, warn,
                                   [{"term": k, "text": t} for k, t in MEANS_ES.items()])
    envelope.progress(100, f"{len(readings)} hermanas en {len(tfs)} timeframes")
    return {"population": population, "panel": panel, "table": table}
