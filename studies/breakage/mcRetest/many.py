"""Every strategy of one ingest, and what can only be said across them, as one result."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.breakage.mcRetest import one, run as study
from studies.breakage.mcRetest.contract import words
from studies.breakage.mcRetest.contract.tabs import COMPOSITE_HELP

COLUMNS = ["strategy", "identity", "verdict", "composite", "binding", "stress_net_p5",
           "stress_cvar_dd_pct", "vetoes", "blocked_by"]
# Parallel to COLUMNS minus "identity" (dropped before the table is drawn) — CONTRACT §2's
# per-column table help (2026-09-30 §6: "?" en «Veredicto compuesto» y en «qué falló»).
SHOWN_HELP = [None, None, COMPOSITE_HELP, None, None, None,
             "Qué veto de gates.py mandó el veredicto a FAIL.",
             "Qué veto SOLO de datos lo dejó en INCONCLUSIVE, sin decidir nada."]


def table(members: list[dict]) -> pd.DataFrame:
    """One row per strategy, worst composite first."""
    return pd.DataFrame([{"strategy": m["strategy"], "identity": m["identity"],
                          **m["summary"]} for m in members])[COLUMNS].sort_values("composite")


def population(result: dict, members: list[dict], cfg: dict, started: float) -> dict:
    """The ingest read as one result: the verdicts, the cross-strategy facts, the caveat."""
    rows = table(members)
    passed = int(rows.verdict.isin(["STRONG", "ACCEPTABLE", "MARGINAL"]).sum())
    counts = rows.verdict.value_counts()
    strategy_table = blocks.table("Estrategia a estrategia", rows.drop(columns=["identity"]))
    strategy_table["help"] = SHOWN_HELP
    tabs = [envelope.tab("summary", "Veredictos", [
        {"kind": "bars", "title": "Veredictos", "unit": "estrategias", "reference": None,
         "items": [{"label": v, "value": int(counts.get(v, 0)), "error": None,
                    "state": words.STATE[v]} for v in words.VERDICTS]},
        strategy_table]),
        envelope.tab("battery", "De la batería entera", [blocks.table(
            "Lo que sólo se dice mirando todas", pd.DataFrame(
                words.battery(result), columns=["qué", "valor", "qué significa"]))],
            note="Los umbrales de gates.py son valores por defecto del config.yaml y nadie "
                 "los ha calibrado contra la operativa real. Si fallan todas, mira primero el "
                 "umbral: se mueve con --set gates.survival_dd_pct=0.35.")]
    verdict = blocks.verdict(
        f"{passed} de {len(rows)}", "pass" if passed else "fail",
        "Ocho tareas, cada una perturbando una sola cosa, N re-ejecuciones completas del "
        "backtest en cada una (N = `mc_retest.simulations`). La pregunta no es si la curva "
        "fue suerte, sino si habría "
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
    result = study.battery(inputs["keys"], inputs["provenance"], inputs["trades"],
                          inputs["asset"], cfg)
    members = [one.contract(got, inputs, cfg, started)
               for _, got in sorted(result["strategies"].items())]
    envelope.progress(100, f"{len(members)} estrategias")
    return {"population": population(result, members, cfg, started), "members": members}
