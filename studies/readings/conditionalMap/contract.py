"""The conditional map's two tabs — both descriptive, neither carries a verdict."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.conditionalMap import cells, regime, sessions

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


def _bars(title: str, rows: list[dict], names: dict | None = None) -> dict:
    """One bar per populated label, with its interval — the shape both one-cut views share."""
    return {"kind": "bars", "title": title, "unit": "USD", "reference": None,
            "items": [{"label": (names or {}).get(r["label"], r["label"]),
                       "value": round(r["mean"], 2),
                       "error": [round(r["ci_lo"], 2), round(r["ci_hi"], 2)], "state": "info"}
                      for r in rows]}


def _rows(rows: list[dict], key: str, names: dict | None = None) -> pd.DataFrame:
    """The table behind one bars block."""
    return _table([{key: (names or {}).get(r["label"], r["label"]), "operaciones": r["n"],
                    "pnl_medio": round(r["mean"], 2), "acierto": round(r["hit_rate"], 3)}
                   for r in rows], [key, "operaciones", "pnl_medio", "acierto"])


def calendar_tab(got: dict, cfg: dict) -> dict:
    """Mean P&L per trade by session and by weekday — together, and each on its own.

    The three blocks are the three views the window switches between: session x weekday,
    sessions alone, weekdays alone. Cells and labels below the floor are left out.
    """
    pnl, found, boot = got["pnl"], got["found"], cfg["bootstrap"]
    both = cells.session_by_weekday(pnl, found["session"], found["weekday"], boot)
    by_session = cells.by_label(pnl, found["session"], sessions.ORDER, boot)
    by_day = cells.by_label(pnl, found["weekday"], cells.WEEKDAYS, boot)
    hours = cfg["sessions"]
    unplaced = int((found["session"] == "").sum())
    grid = [{"kind": "grid", "title": "P&L medio por operación (USD) — sesión x día",
             "rows": list(sessions.ORDER), "cols": [WEEKDAY_ES[d] for d in cells.WEEKDAYS],
             "values": both["mean"], "scale": "diverging", "levels": None,
             "labels": None}] if both["cells"] else []
    crossed = "" if both["cells"] else (f" Ninguna casilla sesión x día llega a {cells.MIN_CELL} "
                                         "operaciones: el cruce no se enseña.")
    return envelope.tab("calendario", "Sesión y día de la semana", grid + [
        _bars("Por sesión (USD)", by_session),
        blocks.table("Cada sesión", _rows(by_session, "sesión")),
        _bars("Por día de la semana (USD)", by_day, WEEKDAY_ES),
        blocks.table("Cada día", _rows(by_day, "día", WEEKDAY_ES))],
        note=f"Hora de entrada llevada del reloj del feed a UTC y de ahí a la hora local de "
             f"cada ciudad: Tokio {hours['asia']['open']}-{hours['asia']['close']}, Londres "
             f"{hours['london']['open']}-{hours['london']['close']}, Nueva York "
             f"{hours['new_york']['open']}-{hours['new_york']['close']}. El día de la semana "
             f"es el del reloj del feed. {unplaced} operaciones caen en una hora que el cambio "
             f"de horario repite o salta, y no se asignan a ninguna sesión.{crossed}")
