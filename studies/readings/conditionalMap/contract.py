"""The conditional map's two tabs — both descriptive, neither carries a verdict."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.conditionalMap import cells, regime

MULTIPLE_COMPARISONS = {
    "code": "multiple_comparisons", "state": "info",
    "text": "Este mapa fabrica hipótesis, no las comprueba (PDF del dueño, item 6 — "
            "TRADE_LEVEL_TESTS). Con tres cortes y varias celdas por corte, alguna sale "
            "significativa por azar en cualquier estrategia, incluida una sin ninguna "
            "ventaja. Ninguna celda de aquí es un filtro: uno nuevo se anota en el ledger "
            "(encargo 8) y se revalida sobre datos que no se hayan mirado."}

WEEKDAY_ES = {"Monday": "lunes", "Tuesday": "martes", "Wednesday": "miércoles",
              "Thursday": "jueves", "Friday": "viernes"}

GLOSSARY = [
    {"term": "Tercil de volatilidad", "text": "ATR diario cortado en tres partes iguales "
     "sobre el tramo de construcción, y congelado ahí: cada operación se compara contra "
     "esos dos cortes, nunca contra los de su propia muestra."},
    {"term": "Tercil de tendencia", "text": "Ratio de eficiencia |cierre_t − cierre_t−n| / "
     "Σ|Δcierre| sobre el mismo tramo congelado — 1 es un movimiento recto, cerca de 0 es "
     "ruido en torno a una media plana."},
    {"term": "Intervalo", "text": "Bootstrap percentil sobre el P&L medio de la celda "
     "(core.surface.dedupe.bootstrap_ci)."},
    {"term": "Celda vacía", "text": f"Menos de {cells.MIN_CELL} operaciones — el mismo suelo "
     "que la puerta OOS (engines/nulls/config.yaml#verdict.min_trades); no se enseña ni se "
     "juzga."}]


def _table(rows: list[dict], columns: list[str]) -> pd.DataFrame:
    """A DataFrame with the right columns even when no cell cleared the floor."""
    return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)


def regime_tab(got: dict, cfg: dict) -> dict:
    """Mean P&L per trade over volatility x tendencia; cells below the floor left blank."""
    table = cells.grid(got["pnl"], got["vol_idx"], got["trend_idx"], cfg["bootstrap"])
    rows = [{"volatilidad": r["volatilidad"], "tendencia": r["tendencia"],
             "operaciones": r["n"], "pnl_medio": round(r["mean"], 2),
             "ci_baja": round(r["ci_lo"], 2), "ci_alta": round(r["ci_hi"], 2),
             "acierto": round(r["hit_rate"], 3)} for r in table["cells"]]
    return envelope.tab("regimen", "Volatilidad x tendencia en la entrada", [
        {"kind": "grid", "title": "P&L medio por operación (USD)", "rows": list(regime.BUCKETS),
         "cols": list(regime.BUCKETS), "values": table["mean"], "scale": "diverging",
         "levels": None, "labels": None},
        blocks.table("Celda a celda", _table(rows, ["volatilidad", "tendencia", "operaciones",
                                                     "pnl_medio", "ci_baja", "ci_alta",
                                                     "acierto"]))],
        note=f"Terciles congelados sobre el tramo de construcción de "
             f"{cfg['run']['symbol']}. ATR({cfg['volatility']['atr_period']}) para la "
             f"volatilidad — cortes {[round(float(e), 4) for e in got['vol_edges']]}. Ratio "
             f"de eficiencia a {cfg['trend']['window']} días para la tendencia — cortes "
             f"{[round(float(e), 4) for e in got['trend_edges']]}.")


def calendar_tab(got: dict, cfg: dict) -> dict:
    """Mean P&L per trade by weekday; days below the floor left out."""
    rows = cells.by_weekday(got["pnl"], got["found"]["weekday"], cfg["bootstrap"])
    return envelope.tab("calendario", "Día de la semana", [
        {"kind": "bars", "title": "P&L medio por operación (USD)", "unit": "USD",
         "reference": None,
         "items": [{"label": WEEKDAY_ES[r["weekday"]], "value": round(r["mean"], 2),
                    "error": [round(r["ci_lo"], 2), round(r["ci_hi"], 2)], "state": "info"}
                   for r in rows]},
        blocks.table("Cada día", _table(
            [{"día": WEEKDAY_ES[r["weekday"]], "operaciones": r["n"],
              "pnl_medio": round(r["mean"], 2), "acierto": round(r["hit_rate"], 3)}
             for r in rows], ["día", "operaciones", "pnl_medio", "acierto"]))],
        note="Sesión (Asia/Londres/Nueva York/solape) no está aquí todavía: el campo "
             "`session` del activo nombra una sesión de SQX que resuelve a la semana de "
             "mercado abierto (p. ej. lunes a viernes 01:05–23:50), no a una partición del "
             "día en zonas horarias — inventar esos cortes está prohibido (CLAUDE.md regla "
             "11). Pendiente de que el dueño fije las horas; ver `_coord/BOARD.md`.")
