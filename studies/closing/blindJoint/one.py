"""One mother at step 20: her three withheld results side by side, and her call under each reading."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.closing.blindJoint import readings, words
from studies.closing.blindJoint.pieces import NAMES, PIECES

MODULE = "blindJoint"
CALL = {"pass": "Pasa", "watch": "Revisar", "fail": "No pasa", "none": "Sin leer"}


def chosen(cfg: dict) -> tuple[str, str] | None:
    """The reading the owner chose, or None while either half is still open."""
    joint = cfg["joint"]
    return (joint["pieces"], joint["population"]) \
        if joint["pieces"] and joint["population"] else None


def parts(row: pd.Series, got: dict) -> list[dict]:
    """The three pieces, each with its own study's state, and the StepM over every entrant."""
    said = [{"label": f"{PIECES[p]} {NAMES[p]}", "state": row[p]["state"],
             "value": row[p]["score"], "note": words.call(row[p]["label"])} for p in PIECES]
    if got["refused"]:
        return said + [{"label": "20 SPA/StepM", "state": "none", "value": None,
                        "note": "sin leer: la política no deja al paso 20 mirar oos2"}]
    named = bool(got["table"].loc[row.name, "named_all"])
    return said + [{"label": "20 SPA/StepM", "state": "pass" if named else "fail",
                    "value": float(got["table"].loc[row.name, "sharpe"]),
                    "note": "nombrada: gana más que sus mismas operaciones entradas al azar"
                            if named else "no nombrada: no se distingue de entrar al azar"}]


def equity_chart(mother: str, got: dict) -> dict:
    """The mother's own oos2 equity next to what her random trader earns on average.

    Args:
        mother: The mother's name, a column of `got["panel"]`.
        got: What measure.run() returned (`panel`, `benchmark`, both on oos2's days).

    Returns:
        A "lines" block: two cumulative curves on the same USD axis; the gap between them
        is the excess the SPA tests.
    """
    mine = got["panel"][mother].cumsum()
    random = got["benchmark"][mother].cumsum()
    return {"kind": "lines", "title": "Equity en oos2: la madre contra su operador al azar",
            "unit": "USD", "x": [d.strftime("%Y-%m-%d") for d in mine.index],
            "series": [{"label": "Madre", "values": [float(v) for v in mine], "role": "real"},
                       {"label": "Operador al azar (media)",
                        "values": [float(v) for v in random], "role": "reference"}],
            "auto_dash_negative": True, "zero_shade": True,
            "note": "El operador al azar hace las mismas operaciones que la madre — cuántas, "
                    "de qué lado, con qué lotes, cuánto dura cada una y a qué coste — pero "
                    "entra en momentos al azar de oos2. La línea es la media de todos ellos: "
                    "lo que da el mercado por estar dentro ese tiempo. Lo que la madre queda "
                    "por encima es lo que vale su entrada."}


def run(row: pd.Series, got: dict, cfg: dict) -> dict:
    """What step 20 says about one mother.

    Args:
        row: One row of `pieces.population`.
        got: What measure.run() returned.
        cfg: What inputs.config() returned.

    Returns:
        The contract dict. An incomplete mother is listed and never read: the verdict says
        which pieces it lacks. A complete one carries her call under the chosen reading,
        or — while the owner has not chosen — `Sin regla` with every reading in a table.
    """
    started = time.time()
    if not row["complete"]:
        missing = ", ".join(f"{PIECES[p]} ({NAMES[p]})" for p in row["missing"])
        said = blocks.verdict("Incompleta", "none",
                              f"Le falta {missing}. El paso 20 es ciego hasta tener las "
                              f"tres piezas, así que no se lee ninguna de las que tiene.")
        return envelope.envelope(MODULE, row.name, row["identity"], cfg, started, [], said,
                                 summary={"complete": False, "call": "none"})
    calls = got["calls"].loc[row.name]
    reading = chosen(cfg)
    state = calls[readings.label(reading)] if reading else "info"
    meaning = (f"Bajo la lectura {words.reading(reading)}: las piezas se combinan por "
               f"{reading[0].replace('_', ' ')} y el StepM cuenta su búsqueda sobre las "
               f"{reading[1]}."
               if reading else
               "Paso 20 es un resumen: no descarta a nadie (dueño, 2026-10-12). Las piezas y el "
               "StepM se enseñan como diagnóstico; abajo, lo que diría cada lectura.")
    said = blocks.verdict(CALL[state] if reading else "Sin regla", state, meaning, None,
                          parts(row, got))
    # The sentences go in a list block, which wraps; a table cell would cut them with «…».
    pieces = blocks.table("Las tres piezas, como las dijo su estudio", pd.DataFrame(
        [[f"{PIECES[p]} {NAMES[p]}", words.call(row[p]["label"]), words.STATE[row[p]["state"]]]
         for p in PIECES], columns=["paso", "llamada", "estado"]))
    pieces["states"] = [[None, None, row[p]["state"]] for p in PIECES]
    says = {"kind": "list", "title": "Qué quiere decir cada una", "note": None,
            "items": [{"title": f"{PIECES[p]} {NAMES[p]} · {words.call(row[p]['label'])}",
                       "text": words.sentence(row[p]["meaning"])} for p in PIECES]}
    tabs = [envelope.tab("pieces", "Las tres piezas", [pieces, says])]
    if not got["refused"]:
        r = got["table"].loc[row.name]
        tabs.append(envelope.tab("benchmark", "Contra el operador al azar en oos2", [
            blocks.table("Contra un operador al azar con su misma huella", pd.DataFrame(
                [["Sharpe anual de la madre", r["sharpe"]],
                 ["Operador al azar, media diaria (USD)", r["random_day"]],
                 ["Exceso medio diario de la madre (USD)", r["excess_day"]],
                 ["Error de simulación del operador al azar (USD/día)", r["mc_day"]]],
                columns=["qué", "valor"]),
                "Exceso positivo = la madre gana más que sus mismas operaciones entradas al "
                "azar. Batirlo es que ese exceso no se explique por suerte, contadas todas las "
                "madres que llegaron (SPA y StepM). El error de simulación es lo que se mueve "
                "la media del azar por haber simulado un número finito de operadores."),
            equity_chart(row.name, got)]))
    return envelope.envelope(MODULE, row.name, row["identity"], cfg, started, tabs, said,
                             summary={"complete": True, "call": state,
                                      **{p: row[p]["state"] for p in PIECES},
                                      **{r: calls[r] for r in calls.index}})
