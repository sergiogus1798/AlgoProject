"""Every mother that reached step 20, read as one result: the four pieces, the readings, the SPA."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.closing.blindJoint import measure, one, readings
from studies.closing.blindJoint.pieces import NAMES, PIECES

LEVEL = {"pass": 1, "watch": 0, "fail": -1, "none": None, "info": None}
MEANING = {"lower": "cuenta a favor todas las madres malas: el suelo de la p",
           "consistent": "la de Hansen: descarta sólo las claramente peores que el benchmark",
           "upper": "cuenta en contra todas las madres malas: el test de White"}


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
    """The SPA's three p-values and each mother against buy and hold, or why they are missing."""
    if got["refused"]:
        return envelope.tab("spa", "SPA y StepM sobre oos2", [], note=(
            f"Sin leer. {got['refused']}. Las piezas de 17-19 sí se leen: no abren oos2, "
            f"leen lo que ya escribieron sus estudios. Para que el paso 20 mire oos2 el dueño "
            f"añade BlindJoint a reserved_for en assets/_policy.yaml."))
    spa, t = got["spa"], got["table"]
    return envelope.tab("spa", "SPA y StepM sobre oos2", [
        blocks.table("Las tres p del SPA de Hansen", pd.DataFrame(
            [[k, spa[k], MEANING[k]] for k in ("lower", "consistent", "upper")],
            columns=["p", "valor", "qué supone"]),
            f"Nula: ninguna de las {got['K']} madres bate al buy & hold a igual riesgo."),
        blocks.table("Cada madre contra el buy & hold", t.reset_index(names="madre")[
            ["madre", "sharpe", "excess_day", "lots_bh", "named_all"]].rename(columns={
                "excess_day": "exceso USD/día", "lots_bh": "lotes B&H",
                "named_all": "StepM (entrantes)"}),
            f"Sharpe del buy & hold {got['sharpe_bh']:.3f}; FWER {cfg['stepm']['fwer']}; "
            f"{got['days']} días; bloque medio {got['block']} días.")],
        note="Datos que ninguna criba miró: la curva diaria marcada a mercado de cada madre, "
             "su propio retest en oos2.")


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
        return blocks.verdict(f"{n} de {complete} pasan el paso 20", "pass" if n else "fail",
                              f"Lectura {readings.label(reading)}.", None, parts)
    sure = [readings.label(r) for r in readings.names()
            if not readings.kept(got["states"], r[0])]
    return blocks.verdict(
        "SIN REGLA", "info",
        "El dueño no ha elegido cómo se combinan las piezas ni sobre quién cuenta el StepM. "
        f"Descartan a todas por las piezas, sin llegar al StepM: {', '.join(sure) or 'ninguna'}.",
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
    calls = got["calls"]
    word = calls.apply(lambda col: col.map(one.CALL))
    incomplete = population[~population["complete"]]
    tabs = [
        envelope.tab("pieces", "Las cuatro piezas, a la vez", [
            grid("Qué dijo cada estudio", got["states"].rename(columns={
                p: f"{PIECES[p]} {NAMES[p]}" for p in PIECES}), labels,
                "Azul oscuro pasa, azul medio a medias (indeciso, ciego), blanco no pasa. El "
                "estado es el del propio estudio: el paso 20 no re-deriva ningún umbral.")],
            note=data["source"]),
        envelope.tab("readings", "La llamada bajo cada lectura", [
            grid("Lecturas × madres", calls.T, word.T,
                 "piezas+población. Pasa quien sobrevive a las piezas Y el StepM la nombra "
                 "sobre esa población. Sin color: el StepM no corrió.")]),
        spa_tab(got, cfg)]
    warnings = ([{"code": "policy", "state": "watch", "text": got["refused"]}]
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
        glossary=[{"term": "paso 20", "text": "La lectura conjunta y ciega de WFC, CSCV, "
                                              "superficies por mercado y WFM, que no se miran "
                                              "hasta que las cuatro existen."},
                  {"term": "lectura", "text": "Cómo se combinan las cuatro piezas y sobre "
                                              "quién cuenta el StepM; decisión del dueño."},
                  {"term": "StepM", "text": "Romano y Wolf: qué madres concretas baten al "
                                            "buy & hold controlando el error de la familia."}])
    members = [one.run(row, got, cfg) for _, row in population.iterrows()]
    envelope.progress(100, result["verdict"]["label"])
    return {"population": result, "members": members, "measured": got}
