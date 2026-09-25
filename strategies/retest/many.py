"""Every strategy of one ingest, and what can only be said across them, as one result."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from strategies.retest import one, run as study
from strategies.retest.contract import words

COLUMNS = ["strategy", "identity", "verdict", "composite", "binding", "stress_net_p5",
           "stress_cvar_dd_pct", "vetoes", "blocked_by"]


def table(members: list[dict]) -> pd.DataFrame:
    """One row per strategy, worst composite first."""
    return pd.DataFrame([{"strategy": m["strategy"], "identity": m["identity"],
                          **m["summary"]} for m in members])[COLUMNS].sort_values("composite")


def population(result: dict, members: list[dict], cfg: dict, started: float) -> dict:
    """The ingest read as one result: the verdicts, the cross-strategy facts, the caveat."""
    rows = table(members)
    passed = int(rows.verdict.isin(["STRONG", "ACCEPTABLE", "MARGINAL"]).sum())
    counts = rows.verdict.value_counts()
    tabs = [envelope.tab("summary", "Veredictos", [
        {"kind": "bars", "title": "Veredictos", "unit": "estrategias", "reference": None,
         "items": [{"label": v, "value": int(counts.get(v, 0)), "error": None,
                    "state": words.STATE[v]} for v in words.VERDICTS]},
        blocks.table("Estrategia a estrategia", rows.drop(columns=["identity"]))]),
        envelope.tab("battery", "De la batería entera", [blocks.table(
            "Lo que sólo se dice mirando todas", pd.DataFrame(
                words.battery(result), columns=["qué", "valor", "qué significa"]))],
            note="Los umbrales de gates.py son valores por defecto del config.yaml y nadie "
                 "los ha calibrado contra la operativa real. Si fallan todas, mira primero el "
                 "umbral: se mueve con --set gates.survival_dd_pct=0.35.")]
    verdict = blocks.verdict(
        f"{passed} de {len(rows)}", "pass" if passed else "fail",
        "Ocho tareas, cada una perturbando una sola cosa, mil re-ejecuciones completas del "
        "backtest en cada una. La pregunta no es si la curva fue suerte, sino si habría "
        "existido.")
    return envelope.envelope(one.MODULE, None, None, cfg, started, tabs, verdict)


def run(inputs: dict, cfg: dict) -> dict:
    """Every strategy of the ingest, one process each.

    Args:
        inputs: What load.load() returned.
        cfg: What config.load() returned.

    Returns:
        {"population": the ingest's result, "members": one result per strategy}.
    """
    started = time.time()
    envelope.progress(5, "leyendo el ingest y repartiendo estrategias")
    result = study.battery(inputs["keys"], inputs["provenance"], cfg)
    members = [one.contract(got, inputs, cfg, started)
               for _, got in sorted(result["strategies"].items())]
    envelope.progress(100, f"{len(members)} estrategias")
    return {"population": population(result, members, cfg, started), "members": members}
