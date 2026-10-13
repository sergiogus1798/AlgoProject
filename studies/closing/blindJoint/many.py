"""Every mother that reached step 20, read as one result: the three pieces, the readings, the SPA."""

import time

import pandas as pd

from core import fanout
from core.study import blocks, result as envelope
from studies.closing.blindJoint import measure, one, readings, words
from studies.closing.blindJoint.pieces import NAMES, PIECES

LEVEL = {"pass": 1, "watch": 0, "fail": -1, "none": None, "info": None}
MEANING = {"lower": "cuenta a favor todas las madres malas: el suelo de la p",
           "consistent": "la de Hansen: descarta sólo las claramente peores que el benchmark",
           "upper": "cuenta en contra todas las madres malas: el test de White"}


_SHARED: dict = {}     # set by `run` before the fork, read by `_member` in the workers


def _member(i: int) -> dict:
    """Mother `i` of the population read, in a worker that inherited what step 20 measured."""
    return one.run(_SHARED["rows"][i], _SHARED["got"], _SHARED["cfg"])


def grid(title: str, frame: pd.DataFrame, labels: pd.DataFrame, note: str) -> dict:
    """States as a three-step grid: no pasa −1, a medias 0, pasa 1, each cell its own word.

    The cuts send the three steps to the two ends and the middle of the nine-step scale, so
    they read apart at a glance: white, mid blue, navy.
    """
    return {"kind": "grid", "title": title, "rows": list(frame.index),
            "cols": list(frame.columns),
            "values": [[LEVEL[s] for s in row] for row in frame.itertuples(index=False)],
            "scale": "sequential", "levels": [-0.5] * 4 + [0.5] * 4,
            "labels": [list(row) for row in labels.itertuples(index=False)], "note": note}


def spa_tab(got: dict, cfg: dict) -> dict:
    """The SPA's three p-values and each mother against her random trader, or why they are missing."""
    if got["refused"]:
        return envelope.tab("spa", "SPA y StepM sobre oos2", [], note=(
            f"Sin leer. {got['refused']}. Las piezas de 17-19 sí se leen: no abren oos2, "
            f"leen lo que ya escribieron sus estudios. Si quien se niega es la política, el "
            f"dueño añade BlindJoint a reserved_for en assets/_policy.yaml."))
    spa, t = got["spa"], got["table"]
    return envelope.tab("spa", "SPA y StepM sobre oos2", [
        blocks.table("Las tres p del SPA de Hansen", pd.DataFrame(
            [[k, spa[k], MEANING[k]] for k in ("lower", "consistent", "upper")],
            columns=["p", "valor", "qué supone"]),
            f"Nula: ninguna de las {got['K']} madres gana más que un operador al azar con su "
            f"misma huella (mismas operaciones, lado, lotes, duración y coste; entrada al azar)."),
        blocks.table("Cada madre contra su operador al azar", t.reset_index(names="madre")[
            ["madre", "sharpe", "excess_day", "random_day", "mc_day", "named_all"]].rename(
                columns={"excess_day": "exceso USD/día", "random_day": "azar USD/día",
                         "mc_day": "error simulación", "named_all": "StepM (entrantes)"}),
            f"Azar = media de {cfg['benchmark']['draws']} operadores al azar (peldaño "
            f"{cfg['benchmark']['rung']}); FWER {cfg['stepm']['fwer']}; "
            f"{got['days']} días; bloque medio {got['block']} días.")],
        note="Datos que ninguna criba miró: el resultado diario de cada madre de cierre a "
             "cierre, reconstruido con las operaciones de su retest en oos2 y las barras M1.")


def headline(got: dict, cfg: dict, complete: int) -> dict:
    """The population's verdict: under the chosen reading, or every reading's count."""
    reading = one.chosen(cfg)
    counts = {r: int((got["calls"][r] == "pass").sum()) for r in got["calls"].columns}
    # A reading is undecided only where a call is still unread; when the pieces already
    # dropped everyone, the StepM that did not run could not have saved anyone.
    open_ = {r: bool((got["calls"][r] == "none").any()) for r in got["calls"].columns}
    parts = [{"label": r, "state": "none" if open_[r] else "pass" if n else "fail",
              "value": None if open_[r] else n,
              "note": f"de {complete} completas" + (" · sin leer el StepM" if open_[r] else "")}
             for r, n in counts.items()]
    if reading:
        n = counts[readings.label(reading)]
        review = int((got["calls"][readings.label(reading)] == "watch").sum())
        return blocks.verdict(f"{n} de {complete} pasan el paso 20",
                              "pass" if n else "watch" if review else "fail",
                              f"Lectura {words.reading(reading)}."
                              + f" {review} a revisar." * bool(review), None, parts)
    sure = [readings.label(r) for r in readings.names()
            if not readings.kept(got["states"], r[0])]
    return blocks.verdict(
        "Sin regla", "info",
        "El dueño no ha elegido cómo se combinan las piezas ni sobre quién cuenta el StepM. "
        f"Descartan a todas por las piezas, sin llegar al StepM: {', '.join(words.reading(tuple(r.split('+'))) for r in sure) or 'ninguna'}.",
        None, parts)


def run(data: dict, cfg: dict) -> dict:
    """Step 20 over every mother that reached it.

    Args:
        data: As measure.run() takes it, plus `source` for the page's note.
        cfg: What inputs.config() returned.

    Returns:
        {"population", "members", "measured"}.
    """
    started = time.time()
    population = data["population"]
    envelope.progress(5, f"{len(population)} madres llegaron al paso 20")
    got = measure.run(data, cfg)
    complete = population[population["complete"]]
    labels = pd.DataFrame({p: complete[p].map(lambda s: s["label"]) for p in PIECES})
    incomplete = population[~population["complete"]]
    tabs = [
        envelope.tab("pieces", "Las tres piezas, a la vez", [
            grid("Qué dijo cada estudio", got["states"].rename(columns={
                p: f"{PIECES[p]} {NAMES[p]}" for p in PIECES}), labels,
                "Azul oscuro pasa, azul medio a medias (indeciso, ciego), blanco no pasa. El "
                "estado es el del propio estudio: el paso 20 no re-deriva ningún umbral.")],
            note=data["source"]),
        spa_tab(got, cfg)]
    warnings = ([{"code": "policy", "state": "watch",
                  "text": f"Falta el StepM: no se pudo calcular ({got['refused']}). El veredicto sale "
                          f"sólo de los tres estados; no hay contraste con el operador al azar en oos2."}]
                if got["refused"] else []) + [
        {"code": "incomplete", "state": "watch",
         "text": f"{m}: le falta {', '.join(NAMES[p] for p in r['missing'])}; no se lee"}
        for m, r in incomplete.iterrows()] + (
        [{"code": "flat", "state": "watch", "text": f"{len(got['flat'])} madres sin movimiento "
                                                    f"en oos2 quedan fuera del test"}]
        if got.get("flat") else [])
    result = envelope.envelope(
        one.MODULE, None, None, cfg, started, tabs, headline(got, cfg, len(complete)),
        warnings=warnings,
        glossary=[{"term": "paso 20", "text": "La lectura conjunta y ciega de WFC, CSCV "
                                              "y WFM, que no se miran "
                                              "hasta que las tres existen."},
                  {"term": "lectura", "text": "Cómo se combinan las tres piezas y sobre "
                                              "quién cuenta el StepM; decisión del dueño."},
                  {"term": "StepM", "text": "Romano y Wolf: qué madres concretas baten a su "
                                            "operador al azar controlando el error de la "
                                            "familia."},
                  {"term": "operador al azar", "text": "Las mismas operaciones de la madre — "
                   "número, lado, lotes, duración y coste — entradas en momentos al azar de "
                   "oos2. Su media es lo que paga el mercado por estar dentro; descuenta la "
                   "deriva del activo sin exigir batir a un largo apalancado."}])
    _SHARED.update(rows=[row for _, row in population.iterrows()], got=got, cfg=cfg)
    done = dict(fanout.run(_member, {i: 1 for i in range(len(population))}, fanout.CORES))
    members = [done[i] for i in range(len(population))]
    envelope.progress(100, result["verdict"]["label"])
    return {"population": result, "members": members, "measured": got}
