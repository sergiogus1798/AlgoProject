"""The gate over one harvest: every level in order, and the population read as one result."""

import time
from typing import Any, TypedDict

import pandas as pd

from core.study import blocks, result as envelope
from engines.inference import localfdr
from studies.screening.gate import cascade, measures, one
from studies.screening.gate.redundancy import medoides, redundancia


class Gate(TypedDict):
    """The gate's result: the population page, each member, the scorecard, the funnel, the null."""
    population: dict[str, Any]
    members: list[dict[str, Any]]
    scores: pd.DataFrame
    funnel: pd.DataFrame
    fdr: dict[str, float | None]


def run(data: dict, cfg: dict, rules: list[dict], source: dict, start: str = "0") -> Gate:
    """The cascade, the funnel, and every strategy's own reading.

    Args:
        data: What inputs.staged() returned.
        cfg: What inputs.config() returned.
        rules: Step 8's rules, resolved for the project: the judge's own.
        source: What the manifest records: project, databank, harvest, split, end.
        start: The level to resume at (`cascade.run`).

    Returns:
        {"population", "members", "scores", "funnel", "fdr"}. The scorecard carries the levels'
        facts, the measured columns (`measures`), `p_fdr` (localfdr over the z_mono of whoever
        reached level 3c; a column, no rule cuts on it) and, for whoever stands, `redundancia_value`
        and `redundancia_note`: how many of them share its structure. Nothing is dropped for it.
        Rows come ordered: survivors first, by `p_fdr` descending, ties and empties by `z_mono`.
        `fdr` is the null's three figures and the z it read.
    """
    started = time.time()
    envelope.progress(5, f"{len(data['metrics'])} emparejadas, {len(data['missing'])} sin OOS")
    scores, funnel = cascade.run(data, cfg, rules, start)
    scores = scores.join(measures.table(data))
    z = scores["z_mono"].dropna().astype(float)       # whoever reached level 3c
    fdr = localfdr.fit(z.to_numpy())
    scores["p_fdr"] = pd.Series(fdr["p"], index=z.index, dtype=float)
    scores = scores.sort_values(["survives", "p_fdr", "z_mono"], ascending=False, na_position="last")
    figures = (f" Probabilidad de no ser nula (p_fdr), con la nula empírica de las {len(z)} z que llegaron al "
               f"mono: δ₀ {fdr['delta0']:.3f}, σ₀ {fdr['sigma0']:.3f}, π₀ {fdr['pi0']:.3f}."
               if fdr["p"] is not None else f" Sin p_fdr: {fdr['reason']}.")
    alive = scores.index[scores["survives"]].intersection(data["metrics"].index)
    scores[["redundancia_value", "redundancia_note", "redundancia_grupo"]] = None  # nobody standing
    scores["medoide"] = False
    if len(alive):
        same = redundancia(data, alive, {})
        scores[["redundancia_value", "redundancia_note"]] = same[["value", "note"]]
        medoid = medoides(data["metrics"], data["oos"], alive)
        scores["redundancia_grupo"], scores["medoide"] = medoid["grupo"], medoid["medoide"].reindex(scores.index, fill_value=False)
    rows = funnel.to_dict("records")
    stand = int(scores["survives"].sum())
    doubt = int((scores["limbo"].fillna("") != "").sum())
    population = envelope.envelope(
        one.MODULE, None, None, cfg, started,
        [envelope.tab("funnel", "El embudo", [
            {"kind": "bars", "title": "Cuántas caen en cada regla", "unit": "estrategias",
             "reference": None, "items": [
                 {"label": f"{r['level']} · {r['screen']}", "value": int(r["died"]), "error": None,
                  "state": "fail"} for r in rows]},
            blocks.table("Nivel a nivel, regla a regla", pd.DataFrame(
                [[r["level"], r["screen"], r["entered"], r["limbo"], r["died"]] for r in rows],
                columns=pd.Index(["nivel", "regla", "entran", "limbo", "caen"])))],
            note=f"Cosecha {source['harvest']} · fuera de muestra {source['split']} → "
                 f"{source['end']} · {len(scores)} entran ({source['missing_oos']} sin "
                 f"resultado OOS). Las reglas son las del paso 8 de criteria.yaml; cada "
                 f"estrategia sale en su primer Falla"
                 + ("" if cfg["cascade"]["on"] else " (cascada apagada: se calcula todo para "
                                                    "todas)") + "." + figures)],
        blocks.verdict(f"{stand} de {len(scores)} siguen, {doubt} en limbo",
                       "pass" if stand else "fail",
                       "Una estrategia sigue si ninguna regla del paso 8 le da Falla, nivel a "
                       "nivel, cada uno sobre lo que dejó el anterior."))
    members = [one.run(identity, scores, cfg) for identity in scores.index]
    envelope.progress(100, f"{stand} de {len(scores)} siguen")
    null: dict[str, float | None] = {k: fdr[k] for k in ("delta0", "sigma0", "pi0")}
    null["z"] = len(z)
    return Gate(population=population, members=members, scores=scores, funnel=funnel,
                fdr=null)
