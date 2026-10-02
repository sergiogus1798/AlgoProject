"""The gate over one harvest: every screen in order, and the population read as one result."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.screening.gate import cascade, measures, one


def run(data: dict, cfg: dict, source: dict) -> dict:
    """The cascade, the funnel, and every strategy's own reading.

    Args:
        data: What inputs.load() returned, with the null config and bars added.
        cfg: What inputs.config() returned.
        source: What the manifest records: project, databank, harvest, split, end.

    Returns:
        {"population", "members", "scores", "funnel"}. The thresholds are printed beside
        every screen, because a funnel read without them says nothing.
    """
    started = time.time()
    envelope.progress(5, f"{len(data['metrics'])} emparejadas, {len(data['missing'])} sin OOS")
    scores, funnel = cascade.run(data, cfg)
    scores = scores.join(measures.table(data))
    why = {s["name"]: s for s in cfg["screens"]}
    survive = int(scores["survives"].sum())
    population = envelope.envelope(
        one.MODULE, None, None, cfg, started,
        [envelope.tab("funnel", "El embudo", [
            {"kind": "bars", "title": "Cuántas mata cada criba", "unit": "estrategias",
             "reference": None, "items": [
                 {"label": f"{r.screen} ({r.kind})", "value": int(r.died), "error": None,
                  "state": "fail" if r.kind == "hard" else "watch"}
                 for r in funnel.itertuples()]},
            blocks.table("Criba a criba", pd.DataFrame(
                [[r.screen, r.kind, r.entered, r.passed, r.died,
                  str({k: v for k, v in why[r.screen].items()
                       if k not in ("name", "kind", "why")})]
                 for r in funnel.itertuples()],
                columns=["criba", "tipo", "entran", "pasan", "mueren", "umbrales"])),
            blocks.table("Por qué existe cada criba", pd.DataFrame(
                [[s["name"], " ".join(s["why"].split())] for s in cfg["screens"]],
                columns=["criba", "por qué"]))],
            note=f"Cosecha {source['harvest']} · fuera de muestra {source['split']} → "
                 f"{source['end']} · {len(scores)} entran ({source['missing_oos']} sin "
                 f"resultado OOS). Umbrales deliberadamente laxos (2026-09-23): dice cuánta "
                 f"población mata cada criba, no qué estrategia conservar.")],
        blocks.verdict(f"{survive} de {len(scores)} sobreviven", "pass" if survive else "fail",
                       "Una estrategia sobrevive si pasa todas las cribas duras, en orden, "
                       "cada una sobre lo que dejó la anterior."))
    members = [one.run(identity, scores, cfg) for identity in scores.index]
    envelope.progress(100, f"{survive} de {len(scores)} sobreviven")
    return {"population": population, "members": members, "scores": scores, "funnel": funnel}
