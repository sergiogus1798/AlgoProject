"""One mother at step 20: her four withheld results side by side, and her call under each reading."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.closing.blindJoint import readings
from studies.closing.blindJoint.pieces import NAMES, PIECES

MODULE = "blindJoint"
CALL = {"pass": "PASA", "fail": "NO PASA", "none": "SIN LEER"}


def chosen(cfg: dict) -> tuple[str, str] | None:
    """The reading the owner chose, or None while either half is still open."""
    joint = cfg["joint"]
    return (joint["pieces"], joint["population"]) \
        if joint["pieces"] and joint["population"] else None


def parts(row: pd.Series, got: dict) -> list[dict]:
    """The four pieces, each with its own study's state, and the StepM over every entrant."""
    said = [{"label": f"{PIECES[p]} {NAMES[p]}", "state": row[p]["state"],
             "value": row[p]["score"], "note": row[p]["label"]} for p in PIECES]
    if got["refused"]:
        return said + [{"label": "20 SPA/StepM", "state": "none", "value": None,
                        "note": "sin leer: la política no deja al paso 20 mirar oos2"}]
    named = bool(got["table"].loc[row.name, "named_all"])
    return said + [{"label": "20 SPA/StepM", "state": "pass" if named else "fail",
                    "value": float(got["table"].loc[row.name, "sharpe"]),
                    "note": "nombrada contra el buy & hold" if named else
                            f"no nombrada; Sharpe del buy & hold {got['sharpe_bh']:.3f}"}]


def equity_chart(mother: str, got: dict, lots_bh: float) -> dict:
    """The mother's own oos2 equity next to buy & hold's, both at the same daily risk.

    Args:
        mother: The mother's name, a column of `got["panel"]`.
        got: What measure.run() returned (`panel`, `held`, both already on oos2's days).
        lots_bh: The buy & hold size measure.equal_risk() found for this mother.

    Returns:
        A "lines" block: two cumulative curves on the same USD axis (feedback §9.2, adding
        the original backtest's own curve beside buy & hold — same risk scaling as the
        stats table above).
    """
    mine = got["panel"][mother].cumsum()
    bh = (got["held"] * lots_bh).cumsum()
    return {"kind": "lines", "title": "Equity en oos2: la madre contra el buy & hold "
            "a igual riesgo", "unit": "USD", "x": [d.strftime("%Y-%m-%d") for d in mine.index],
            "series": [{"label": "Madre", "values": [float(v) for v in mine], "role": "real"},
                       {"label": "Buy & hold (igual riesgo)", "values": [float(v) for v in bh],
                        "role": "reference"}],
            "auto_dash_negative": True, "zero_shade": True,
            "note": "Misma escala de riesgo que la tabla de arriba: lotes de buy & hold "
                    "elegidos para que su volatilidad diaria iguale a la de la madre."}


def run(row: pd.Series, got: dict, cfg: dict) -> dict:
    """What step 20 says about one mother.

    Args:
        row: One row of `pieces.population`.
        got: What measure.run() returned.
        cfg: What inputs.config() returned.

    Returns:
        The contract dict. An incomplete mother is listed and never read: the verdict says
        which pieces it lacks. A complete one carries her call under the chosen reading,
        or — while the owner has not chosen — `SIN REGLA` with every reading in a table.
    """
    started = time.time()
    if not row["complete"]:
        missing = ", ".join(f"{PIECES[p]} ({NAMES[p]})" for p in row["missing"])
        said = blocks.verdict("INCOMPLETA", "none",
                              f"Le falta {missing}. El paso 20 es ciego hasta tener las "
                              f"cuatro piezas, así que no se lee ninguna de las que tiene.")
        return envelope.envelope(MODULE, row.name, row["identity"], cfg, started, [], said,
                                 summary={"complete": False, "call": "none"})
    calls = got["calls"].loc[row.name]
    reading = chosen(cfg)
    state = calls[readings.label(reading)] if reading else "info"
    meaning = (f"Bajo la lectura {readings.label(reading)}: las piezas se combinan por "
               f"{reading[0]} y el StepM cuenta su búsqueda sobre las {reading[1]}."
               if reading else
               "El dueño no ha elegido todavía cómo se combinan las cuatro piezas ni sobre "
               "quién cuenta el StepM (config.yaml, joint). Abajo, lo que diría cada lectura.")
    said = blocks.verdict(CALL[state] if reading else "SIN REGLA", state, meaning, None,
                          parts(row, got))
    pieces = blocks.table("Las cuatro piezas, como las dijo su estudio", pd.DataFrame(
        [[f"{PIECES[p]} {NAMES[p]}", row[p]["label"], row[p]["state"], row[p]["meaning"]]
         for p in PIECES], columns=["paso", "llamada", "estado", "qué quiere decir"]))
    tabs = [envelope.tab("pieces", "Las cuatro piezas", [pieces])]
    if not got["refused"]:
        r = got["table"].loc[row.name]
        tabs.append(envelope.tab("benchmark", "Contra el buy & hold en oos2", [
            blocks.table("Contra el buy & hold a igual riesgo", pd.DataFrame(
                [["Sharpe anual de la madre", r["sharpe"]],
                 ["Sharpe anual del buy & hold", got["sharpe_bh"]],
                 ["Lotes de buy & hold a igual riesgo", r["lots_bh"]],
                 ["Exceso medio diario (USD)", r["excess_day"]]], columns=["qué", "valor"]),
                "Exceso positivo ⇔ Sharpe mayor que el del buy & hold."),
            equity_chart(row.name, got, r["lots_bh"])]))
    return envelope.envelope(MODULE, row.name, row["identity"], cfg, started, tabs, said,
                             summary={"complete": True, "call": state,
                                      **{p: row[p]["state"] for p in PIECES},
                                      **{r: calls[r] for r in calls.index}})
