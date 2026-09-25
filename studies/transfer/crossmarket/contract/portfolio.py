"""The Portfolio tab and the Warnings tab: the combined account, and every reason to distrust."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.transfer.crossmarket.contract import nulls, shared
from studies.transfer.crossmarket.mechanics.curves import COMBINED
from studies.transfer.crossmarket.simulate import metrics

SHOWN = ("ret_dd", "net", "dd", "sharpe", "pf", "losing_run")


def portfolio_tab(record: dict, cfg: dict) -> dict:
    """One strategy in every market it traded, as a single account."""
    p, w = record["portfolio"], record["portfolio"]["whole"]
    dates, placed = shared.on_axis(p["curves"], "pct")
    series = [{"label": "portfolio" if feed == COMBINED else feed, "values": values,
               "role": "real" if feed == COMBINED else "reference"}
              for feed, values in placed.items()]
    return envelope.tab("portfolio", "Portfolio", [
        blocks.table("La cuenta combinada", pd.DataFrame(
            [["beneficio del portfolio (USD)", w["net"]],
             ["peor caída sobre la curva combinada (%)", w["dd_pct"] * 100],
             ["Ret/DD del portfolio", w["ret_dd"]],
             ["tiempo abierto con 2+ posiciones", p["overlap"]["share"]],
             ["posiciones a la vez, como máximo", p["overlap"]["most"]],
             ["operaciones en total", p["trades"]],
             ["periodo", f"{p['from']} … {p['to']}"], ["mercados", len(p["markets"])]],
            columns=["", "valor"])),
        {"kind": "lines", "title": "Equity del portfolio, y qué puso cada mercado en él",
         "unit": "%", "x": dates, "series": series,
         "note": f"Una sola cuenta de {cfg['equity']['starting']:,.0f} $: las líneas finas "
                 f"suman la gruesa. Un mercado bajo cero toda la muestra es uno que los demás "
                 f"cargaban."},
        blocks.table("Qué aporta cada mercado", pd.DataFrame(
            [[m["feed"], m["trades"], *[m["without"][k] for k in SHOWN],
              *[m["delta"][k] for k in SHOWN]] for m in p["marginal"]]
            + [["el portfolio entero", None, *[w[k] for k in SHOWN], *[None] * len(SHOWN)]],
            columns=["se quita…", "operaciones", *[f"{metrics.LABELS[k]} sin él" for k in SHOWN],
                     *[f"Δ {metrics.LABELS[k]}" for k in SHOWN]]),
            "Δ es el portfolio entero menos el portfolio sin ese mercado: Δ positivo = ese "
            "mercado mejora la combinación. Que aporte poco no es un problema; que reste, sí."),
        blocks.table("Cuánto es suerte: bloques de calendario", pd.DataFrame(
            [[metrics.LABELS[k], w[k], p["ci"][k]["median"], p["ci"][k]["lo"],
              p["ci"][k]["hi"]] for k in SHOWN],
            columns=["estadístico", "portfolio real", "mediana remuestreada", "CI 5 %",
                     "CI 95 %"]),
            f"Remuestreo por bloques de {cfg['portfolio']['block_weeks']} semanas: las "
            f"operaciones de todos los mercados de un bloque viajan juntas, porque la "
            f"dependencia que importa es contemporánea."),
        blocks.table("Y si hubieran llegado en otro orden", pd.DataFrame(
            [[metrics.LABELS[k], p["order"][k]["observed"], p["order"][k]["median"],
              p["order"][k]["p"][2.5], p["order"][k]["p"][97.5]]
             for k in SHOWN if k in p["order"]],
            columns=["estadístico", "portfolio real", "mediana barajada", "p2,5", "p97,5"]),
            "Las mismas operaciones barajadas por bloques: el beneficio no puede moverse, "
            "sólo las métricas de camino.")],
        note=f"Una sola cuenta para todos los mercados, {record['base']['feed']} incluido como "
             f"posición núcleo. La caída se mide sobre la curva combinada, nunca sumando. El "
             f"activo base es donde se optimizó, así que el portfolio se ve mejor de lo que es.")


def warnings_tab(record: dict) -> dict:
    """Every market's warnings in four parts; none of them hides a market."""
    return envelope.tab("warnings", "Avisos",
                        [nulls.warnings_table(record["rows"], "Avisos por mercado")],
                        note="Ningún mercado se excluye por esto. Cada aviso dice a qué afecta "
                             "y a qué no, porque casi ninguno invalida la fila entera.")
