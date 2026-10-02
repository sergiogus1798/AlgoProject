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
    {"term": f"< {cells.MIN_CELL} ops", "text": f"Menos de {cells.MIN_CELL} operaciones — el "
     "mismo suelo que la puerta OOS (engines/nulls/config.yaml#verdict.min_trades): la "
     "casilla no enseña su P&L ni se juzga, y lo dice en vez de quedarse en blanco."},
    {"term": "Muestra", "text": "OOS1 lee solo el primer fuera de muestra; Completa, todo el "
     "backtest cosechado (build + OOS1). Más operaciones llenan más casillas, pero la muestra "
     "Completa incluye el tramo en el que se construyó la estrategia: lo que se vea ahí puede "
     "ser parte de lo que la construcción ajustó."}]


SAMPLE_HELP = ("OOS1: solo las operaciones del primer fuera de muestra. Completa: todo lo que "
               "la cosecha tiene de la estrategia — dentro de muestra (build) más OOS1, el "
               "backtest entero que SQX exportó; oos2 no se cosecha. Con más operaciones, más "
               "casillas llegan al suelo; los cortes de tercil son los mismos en las dos.")


def _table(rows: list[dict], columns: list[str]) -> pd.DataFrame:
    """A DataFrame with the right columns even when no cell cleared the floor."""
    return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)


def _selector(by_sample: dict, cfg: dict) -> dict:
    """The «Muestra» drop-down: the configured sample first, the whole harvest beside it."""
    return {"key": "sample", "label": "Muestra", "options": list(by_sample),
            "default": cfg["run"]["sample"], "help": SAMPLE_HELP}


def _grid(title: str, rows: list[str], cols: list[str], table: dict, sample: str) -> list[dict]:
    """The heat map, every cell below the floor written «< N ops» instead of left blank.

    Returns:
        One grid block, or none when no cell clears the floor — a map of nothing but
        blanks has no colour scale to draw.
    """
    if not table["cells"]:
        return []
    labels = [[f"{v:.2f}" if v is not None else f"< {cells.MIN_CELL} ops" for v in row]
              for row in table["mean"]]
    hidden = sum(v is None for row in table["mean"] for v in row)
    return [{"kind": "grid", "title": title, "rows": rows, "cols": cols,
             "values": table["mean"], "scale": "diverging", "levels": None, "labels": labels,
             "select": {"sample": sample},
             "note": (f"Las celdas con menos de {cells.MIN_CELL} operaciones no se muestran: "
                      f"llevan «< {cells.MIN_CELL} ops» ({hidden} de {len(rows) * len(cols)} "
                      "aquí)." if hidden else
                      f"Todas las celdas llegan a {cells.MIN_CELL} operaciones.")}]


def _nothing(cut: str, sample: str) -> dict:
    """Said in place of a map whose every cell is under the floor."""
    return {"kind": "callout", "state": "info", "select": {"sample": sample},
            "text": f"Ninguna casilla {cut} llega a {cells.MIN_CELL} operaciones en la muestra "
                    f"{sample}: el mapa no se enseña."}


def regime_tab(by_sample: dict, cfg: dict) -> dict:
    """Mean P&L per trade over volatility x tendencia, per sample; floored cells say so."""
    shown = []
    for sample, got in by_sample.items():
        table = cells.grid(got["pnl"], got["vol_idx"], got["trend_idx"], cfg["bootstrap"])
        rows = [{"volatilidad": r["volatilidad"], "tendencia": r["tendencia"],
                 "operaciones": r["n"], "pnl_medio": round(r["mean"], 2),
                 "ci_baja": round(r["ci_lo"], 2), "ci_alta": round(r["ci_hi"], 2),
                 "acierto": round(r["hit_rate"], 3)} for r in table["cells"]]
        shown += (_grid("P&L medio por operación (USD)", list(regime.BUCKETS),
                        list(regime.BUCKETS), table, sample)
                  or [_nothing("volatilidad x tendencia", sample)])
        shown.append({**blocks.table(
            "Celda a celda", _table(rows, ["volatilidad", "tendencia", "operaciones",
                                           "pnl_medio", "ci_baja", "ci_alta", "acierto"]),
            f"{len(got['pnl'])} operaciones en la muestra {sample}."),
            "select": {"sample": sample}})
    got = next(iter(by_sample.values()))
    return envelope.tab("regimen", "Volatilidad x tendencia en la entrada", shown,
        [_selector(by_sample, cfg)],
        note=f"Terciles congelados sobre el tramo de construcción de "
             f"{cfg['run']['symbol']}. ATR({cfg['volatility']['atr_period']}) para la "
             f"volatilidad — cortes {[round(float(e), 4) for e in got['vol_edges']]}. Ratio "
             f"de eficiencia a {cfg['trend']['window']} días para la tendencia — cortes "
             f"{[round(float(e), 4) for e in got['trend_edges']]}. En la muestra Completa "
             f"entra el propio tramo de construcción, cuyos días caen un tercio en cada "
             f"tercil por construcción de los cortes.")


def _bars(title: str, found: dict, sample: str, names: dict | None = None) -> dict:
    """One bar per label that clears the floor, with its interval; the rest named in the note."""
    name = (names or {}).get
    hidden = ", ".join(f"{name(k, k)} ({n})" for k, n in found["hidden"].items())
    return {"kind": "bars", "title": title, "unit": "USD", "reference": None,
            "items": [{"label": name(r["label"], r["label"]), "value": round(r["mean"], 2),
                       "error": [round(r["ci_lo"], 2), round(r["ci_hi"], 2)], "state": "info"}
                      for r in found["shown"]],
            "select": {"sample": sample},
            "note": (f"Sin mostrar por tener menos de {cells.MIN_CELL} operaciones: {hidden}."
                     if hidden else "")}


def _rows(found: dict, key: str, sample: str, names: dict | None = None) -> dict:
    """The table behind one bars block."""
    name = (names or {}).get
    return {**blocks.table(key.capitalize() + " a " + key, _table(
        [{key: name(r["label"], r["label"]), "operaciones": r["n"],
          "pnl_medio": round(r["mean"], 2), "acierto": round(r["hit_rate"], 3)}
         for r in found["shown"]], [key, "operaciones", "pnl_medio", "acierto"])),
        "select": {"sample": sample}}


def calendar_tab(by_sample: dict, cfg: dict) -> dict:
    """Mean P&L per trade by session and by weekday — together, and each on its own, per sample.

    The three views the window switches between are session x weekday, sessions alone and
    weekdays alone, once per option of the «Muestra» selector. Cells and labels below the
    floor are not shown, and every one of them says so.
    """
    boot, hours, shown = cfg["bootstrap"], cfg["sessions"], []
    for sample, got in by_sample.items():
        pnl, found = got["pnl"], got["found"]
        both = cells.session_by_weekday(pnl, found["session"], found["weekday"], boot)
        crossed = _grid("P&L medio por operación (USD) — sesión x día", list(sessions.ORDER),
                        [WEEKDAY_ES[d] for d in cells.WEEKDAYS], both, sample)
        by_session = cells.by_label(pnl, found["session"], sessions.ORDER, boot)
        by_day = cells.by_label(pnl, found["weekday"], cells.WEEKDAYS, boot)
        unplaced = int((found["session"] == "").sum())
        shown += (crossed or [_nothing("sesión x día", sample)]) + [
            _bars("Por sesión (USD)", by_session, sample),
            _rows(by_session, "sesión", sample),
            _bars("Por día de la semana (USD)", by_day, sample, WEEKDAY_ES),
            _rows(by_day, "día", sample, WEEKDAY_ES),
            {"kind": "callout", "state": "info", "select": {"sample": sample},
             "text": f"{len(pnl)} operaciones en la muestra {sample}; {unplaced} caen en una "
                     f"hora que el cambio de horario repite o salta y no se asignan a ninguna "
                     f"sesión."}]
    return envelope.tab("calendario", "Sesión y día de la semana", shown,
        [_selector(by_sample, cfg)],
        note=f"Hora de entrada llevada del reloj del feed a UTC y de ahí a la hora local de "
             f"cada ciudad: Tokio {hours['asia']['open']}-{hours['asia']['close']}, Londres "
             f"{hours['london']['open']}-{hours['london']['close']}, Nueva York "
             f"{hours['new_york']['open']}-{hours['new_york']['close']}. El día de la semana "
             f"es el del reloj del feed. Con el volumen tan desigual entre sesiones, partir "
             f"una sola muestra también por día deja muchas casillas por debajo de "
             f"{cells.MIN_CELL} operaciones; la muestra Completa las llena.")
