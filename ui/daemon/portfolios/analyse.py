"""«Analizar»: the selected portfolio (a judged run's contract) or one strategy (its universe column)."""

from typing import Any, cast

import pandas as pd

from ui.daemon.portfolios import construct, parts, shelf

MONTHS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
SEEN = ("build", "oos1")      # a strategy's oos2 is never drawn here: only a verdict opens it
NO_CURVE = ("Esta cartera no tiene curva guardada: su run no ha pasado por el veredicto, que es "
            "quien escribe la curva por tramo y los miembros.")
FUNDED = ("Una run de fondeo guarda cifras de Monte Carlo, no una curva: la P(pasar) y sus reglas "
          "están en «Fondeo». Aquí se ven sus miembros.")


def read(pool: str = "", run: str = "", strategy: str = "", **_: str) -> dict[str, Any]:
    """The tabs of the selected portfolio; of the selected strategy when no portfolio is."""
    if run:
        return portfolio(shelf.folder("runs", run))
    if strategy:
        return single(pool, strategy)
    return parts.empty("No hay nada seleccionado.", "elige abajo una fila de «Carteras» o de «Estrategias».")


def portfolio(folder: shelf.Path) -> dict[str, Any]:
    """Resumen, Curva and Miembros of one run's chosen portfolio."""
    row, known = shelf.run(folder), shelf.names()
    who = ", ".join(shelf.label(i, known) for i in row["members"])
    head = parts.callout(f"{row['id']} · K = {row['k']} [{who}] · {row['label']}",
                         construct.STATE.get(row["pass"], "info"))
    members = parts.table("Miembros", ["estrategia", "símbolo", "marco"],
                          [[shelf.label(i, known), known.get(i, {}).get("symbol", "—"),
                            known.get(i, {}).get("timeframe", "—")] for i in row["members"]])
    out = {"run": row["id"], "relaxed": parts.relaxed(row["relaxed"]), "empty": None}
    if row["kind"] == "funded":
        return out | {"tabs": [parts.tab("Resumen", head, parts.callout(FUNDED), members)]}
    m = shelf.load(folder / "manifest.json")
    doc = shelf.load(folder / "cartera.json") if (folder / "cartera.json").exists() else {"tabs": []}
    drawn = {t["title"]: t["blocks"] for t in doc["tabs"]}
    curve = [dict(b) for b in drawn.get("Cartera", []) if b["kind"] == "lines"]
    for b in curve:      # the members thin and first, the portfolio's segments thick and on top
        full = {shelf.short(i): shelf.label(i, known) for i in row["members"]}
        b["series"] = ([{**s, "role": "sim", "label": full.get(s["label"], s["label"])}
                        for s in b["series"] if s["role"] == "reference"]
                       + [{**s, "role": "real", "label": f"cartera · {s['label']}"}
                          for s in b["series"] if s["role"] != "reference"])
    monthly = [b for b in drawn.get("Cartera", []) if b["kind"] == "table" and "mes" in b["title"]]
    best = m["best"]
    v = shelf.load(folder / "verdict.json") if (folder / "verdict.json").exists() else {}
    oos1 = {**(v.get("oos1") or {}).get("metrics", {}), "sharpe": (v.get("oos1") or {}).get("sharpe"),
            "score": (v.get("oos1") or {}).get("value")}
    stats = parts.table("Las cifras de la cartera, por unidad de riesgo", ["métrica", "build", "oos1", "qué es"],
                        [[construct.HEAD[k], best[k], oos1.get(k), parts.WORDS[k]] for k in construct.METRICS],
                        "Build: donde se eligió. oos1: donde se juzga («—» si aún no se ha juzgado). "
                        "oos2 no se enseña aquí: solo lo abre el veredicto, una vez.")
    lost = parts.callout(NO_CURVE, "watch") if not curve else None
    return out | {"tabs": [parts.tab("Resumen", head, stats, *curve[:1], *monthly, lost),
                           parts.tab("Curva", *curve, lost),
                           parts.tab("Miembros", *[b for b in drawn.get("Cartera", []) if b["kind"] == "table"
                                                   and "mes" not in b["title"]] or [members],
                                     *drawn.get("Universo", []))]}


def single(pool: str, identity: str) -> dict[str, Any]:
    """One strategy from its pool's universe: its curve over build and oos1, its months, its facts."""
    known = shelf.names()
    name = shelf.label(identity, known)
    homes = [p for p in shelf.pools() if identity in p["members"] and (not pool or p["name"] == pool)]
    folders = [f for p in homes for f in shelf.universes(p["hash"])]
    if not folders:
        return parts.empty(f"«{name}» no está en ningún universo construido.", "decláralo en un pool y "
                           "pulsa «Calcular parejas» en Correlación; su ficha completa está en «Archivo» › Importar.")
    folder = folders[0]
    calendar = shelf.load(folder / "manifest.json")["calendar"]
    lo, hi = pd.Timestamp(calendar[SEEN[0]][0]), pd.Timestamp(calendar[SEEN[-1]][1])
    daily = pd.read_parquet(folder / "daily.parquet", columns=[identity])[identity].loc[lo:hi].dropna()
    cut = pd.Timestamp(calendar["oos1"][0])
    total = daily.cumsum()
    series = [{"label": s, "role": "real", "values": [parts.clean(float(v)) if keep else None
                                                      for v, keep in zip(total, mask)]}
              for s, mask in (("build", daily.index < cut), ("oos1", daily.index >= cut))]
    months = pd.read_parquet(folder / "monthly.parquet", columns=[identity])[identity]
    stamps = cast(pd.PeriodIndex, months.index).to_timestamp()
    months = cast(pd.Series, months[(stamps >= lo) & (stamps <= hi)])
    when = cast(Any, months.index)      # a PeriodIndex; the stubs miss its .year and .month
    grid = months.groupby([when.year, when.month]).sum().unstack()
    rows = [[int(y), *[parts.clean(round(float(grid.loc[y].get(m, float("nan"))), 0)) for m in range(1, 13)],
             round(float(grid.loc[y].sum()), 0)] for y in grid.index]
    facts = known.get(identity, {})
    head = parts.callout(f"{name} · {facts.get('symbol', '—')} {facts.get('timeframe', '—')} · paso "
                         f"{facts.get('step', '—')} · universo de «{homes[0]['name']}»")
    line = {"kind": "lines", "title": "P&L acumulado de la estrategia", "unit": "", "series": series,
            "x": [str(d.date()) for d in daily.index],
            "note": "Su curva diaria reconstruida, en la moneda de su backtest archivado, en build y "
                    "oos1. oos2 no se dibuja: solo lo abre un veredicto."}
    table = parts.table("P&L por mes", ["año", *MONTHS, "total"], rows,
                        "Suma del P&L de cada mes, misma moneda, build y oos1.")
    return {"relaxed": "", "empty": None,
            "tabs": [parts.tab("Resumen", head, line, table), parts.tab("Curva", line),
                     parts.tab("Meses", table)]}
