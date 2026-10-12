"""The gate over one harvest: every level in order, and the population read as one result."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.screening.gate import cascade, measures, one
from studies.screening.gate.redundancy import medoides, redundancia


def run(data: dict, cfg: dict, rules: list[dict], source: dict, start: str = "0") -> dict:
    """The cascade, the funnel, and every strategy's own reading.

    Args:
        data: What inputs.staged() returned.
        cfg: What inputs.config() returned.
        rules: Step 8's rules, resolved for the project: the judge's own.
        source: What the manifest records: project, databank, harvest, split, end.
        start: The level to resume at (`cascade.run`).

    Returns:
        {"population", "members", "scores", "funnel"}. The scorecard carries the levels'
        facts, the measured columns (`measures`) and, for whoever stands, `redundancia_value`
        and `redundancia_note`: how many of them share its structure. Nothing is dropped
        for it.
    """
    started = time.time()
    envelope.progress(5, f"{len(data['metrics'])} emparejadas, {len(data['missing'])} sin OOS")
    scores, funnel = cascade.run(data, cfg, rules, start)
    scores = scores.join(measures.table(data))
    alive = scores.index[scores["survives"]].intersection(data["metrics"].index)
    scores[["redundancia_value", "redundancia_note", "redundancia_grupo"]] = None  # nobody standing
    scores["medoide"] = False
    if len(alive):
        same = redundancia(data, alive, {})
        scores[["redundancia_value", "redundancia_note"]] = same[["value", "note"]]
        medoid = medoides(data["metrics"], data["oos"], alive)
        scores["redundancia_grupo"], scores["medoide"] = medoid["grupo"], medoid["medoide"].reindex(scores.index, fill_value=False)
    stand = int(scores["survives"].sum())
    doubt = int((scores["limbo"].fillna("") != "").sum())
    population = envelope.envelope(
        one.MODULE, None, None, cfg, started,
        [envelope.tab("funnel", "El embudo", [
            {"kind": "bars", "title": "Cuántas caen en cada regla", "unit": "estrategias",
             "reference": None, "items": [
                 {"label": f"{r.level} · {r.screen}", "value": int(r.died), "error": None,
                  "state": "fail"} for r in funnel.itertuples()]},
            blocks.table("Nivel a nivel, regla a regla", pd.DataFrame(
                [[r.level, r.screen, r.entered, r.limbo, r.died] for r in funnel.itertuples()],
                columns=["nivel", "regla", "entran", "limbo", "caen"]))],
            note=f"Cosecha {source['harvest']} · fuera de muestra {source['split']} → "
                 f"{source['end']} · {len(scores)} entran ({source['missing_oos']} sin "
                 f"resultado OOS). Las reglas son las del paso 8 de criteria.yaml; cada "
                 f"estrategia sale en su primer Falla"
                 + ("" if cfg["cascade"]["on"] else " (cascada apagada: se calcula todo para "
                                                    "todas)") + ".")],
        blocks.verdict(f"{stand} de {len(scores)} siguen, {doubt} en limbo",
                       "pass" if stand else "fail",
                       "Una estrategia sigue si ninguna regla del paso 8 le da Falla, nivel a "
                       "nivel, cada uno sobre lo que dejó el anterior."))
    members = [one.run(identity, scores, cfg) for identity in scores.index]
    envelope.progress(100, f"{stand} de {len(scores)} siguen")
    return {"population": population, "members": members, "scores": scores, "funnel": funnel}
