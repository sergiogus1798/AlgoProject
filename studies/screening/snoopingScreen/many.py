"""The harvest read as one result: does anything beat buy and hold once the search is paid for."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.screening.snoopingScreen import measure, one

MEANING = {"lower": "cuenta a favor todas las candidatas malas: el suelo de la p",
           "consistent": "la de Hansen: descarta sólo las claramente peores que el benchmark",
           "upper": "cuenta en contra todas las candidatas malas: el test de White, "
                    "el más conservador"}


def run(data: dict, cfg: dict) -> dict:
    """The SPA and the StepM over every paired strategy, and each one's own reading.

    Args:
        data: As measure.run() takes it, plus `source` for the page's note.
        cfg: What inputs.config() returned.

    Returns:
        {"population", "members", "measured"}: the contract dicts and what measure.run()
        returned, which report.py writes and records in the ledger.
    """
    started = time.time()
    envelope.progress(5, f"{data['panel'].shape[1]} estrategias contra el buy & hold")
    got = measure.run(data, cfg)
    t, fwer, spa = got["table"], cfg["stepm"]["fwer"], got["spa"]
    kept = t[t["gate_survives"]]
    beats = int((t["sharpe"] > got["sharpe_bh"]).sum())
    named = len(got["named"])
    src = data["source"]
    note = (f"Cosecha {src['harvest']} · tramo {src['window'][0]} → {src['window'][1]} · "
            f"{got['days']} días · K = {got['K']} estrategias emparejadas, no sólo las "
            f"{len(kept)} que deja la puerta: la puerta eligió sobre este mismo tramo, y un "
            f"test sobre lo que una elección dejó no puede cobrarse esa elección. "
            f"Anota y no elimina (dueño, 2026-09-25).")
    population = envelope.envelope(
        one.MODULE, None, None, cfg, started,
        [envelope.tab("population", "¿Bate alguna al buy & hold?", [
            blocks.table("Las tres p del SPA de Hansen", pd.DataFrame(
                [[k, spa[k], MEANING[k]] for k in ("lower", "consistent", "upper")],
                columns=["p", "valor", "qué supone"]),
                "Hipótesis nula: ninguna de las K bate al buy & hold a igual riesgo. La "
                "distancia entre lower y upper mide cuánto arrastran las candidatas malas."),
            {**blocks.distribution("Sharpe anual de las K, con el del buy & hold marcado", "",
                                   t["sharpe"].values, got["sharpe_bh"],
                                   "Las barras son las K estrategias; la línea, el buy & hold. "
                                   "Las que quedan a su derecha le ganan antes de descontar "
                                   "la búsqueda."), "mark": "buy & hold"},
            blocks.table("Las supervivientes de la puerta", kept.sort_values(
                "sharpe", ascending=False).reset_index()[
                ["strategy", "sharpe", "excess_day", "lots_bh", "superior"]].rename(
                columns={"strategy": "estrategia", "excess_day": "exceso USD/día",
                         "lots_bh": "lotes B&H", "superior": "StepM"})),
            blocks.table("Lo que nombra el StepM", t[t["superior"]].reset_index()[
                ["strategy", "gate_survives", "sharpe", "excess_day"]].rename(
                columns={"strategy": "estrategia", "gate_survives": "pasa la puerta",
                         "excess_day": "exceso USD/día"}),
                f"Con una probabilidad de {fwer} de nombrar al menos una que no bate al "
                f"buy & hold. Vacía es una respuesta, no un fallo.")],
            note=note)],
        blocks.verdict(f"{named} de {got['K']} baten al buy & hold", "pass" if named else "fail",
                       f"El StepM nombra {named} a un FWER de {fwer}; sin descontar la "
                       f"búsqueda, {beats} tienen un Sharpe mayor que el del buy & hold "
                       f"({got['sharpe_bh']:.3f}). SPA consistente: p = {spa['consistent']:.3f}.",
                       None, [{"label": f"SPA {k}", "state": "pass" if spa[k] < fwer else "fail",
                               "value": spa[k], "note": MEANING[k]} for k in spa]),
        warnings=[{"code": "flat", "state": "watch",
                   "text": f"{len(got['flat'])} estrategias sin movimiento en el tramo quedan "
                           f"fuera del test"}] if got["flat"] else [],
        glossary=[{"term": "SPA", "text": "Superior Predictive Ability de Hansen (2005): la p "
                                          "de que ninguna de las K bata al benchmark."},
                  {"term": "StepM", "text": "Romano y Wolf (2005): cuáles concretas lo baten, "
                                            "controlando el error de la familia entera."},
                  {"term": "igual riesgo", "text": "El buy & hold con el tamaño que da a su "
                                                   "P&L diario la volatilidad de la "
                                                   "estrategia."}])
    members = [one.run(identity, got, cfg) for identity in t.index]
    envelope.progress(100, f"{named} de {got['K']} baten al buy & hold")
    return {"population": population, "members": members, "measured": got}
