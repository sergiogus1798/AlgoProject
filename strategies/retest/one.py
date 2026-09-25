"""One strategy's Monte Carlo Retest, returned as the contract's data: what the window paints."""

import time

from core.study import result as envelope
from strategies.retest import run as study
from strategies.retest.contract import tabs
from strategies.retest.inputs import tasks

MODULE = "strategies.retest"
GLOSSARY = [
    {"term": "Control", "text": "La tarea que sólo cambia la barra de inicio. Lo que mueve es "
     "ruido irreducible, y todo coste se mide en múltiplos de su dispersión."},
    {"term": "CVaR del drawdown", "text": "La media del 5 % de peores drawdowns, no su "
     "percentil: lo que pasa cuando pasa lo malo."},
    {"term": "Rejilla", "text": "Una tarea cuyas mil simulaciones dan pocos valores distintos: "
     "sin forma que medir, sólo extremos."},
    {"term": "Bimodal", "text": "Dos grupos de resultados separados: la perturbación a veces "
     "rompe la estrategia y a veces no la toca."}]


def contract(got: dict, inputs: dict, cfg: dict, started: float) -> dict:
    """What run.one() concluded, as the contract dict.

    Args:
        got: What run.one() returned for one strategy.
        inputs: What load.load() returned.
        cfg: What config.load() returned.
        started: When the computation began.

    Returns:
        Verdict, five tabs, glossary and the summary row.
    """
    return envelope.envelope(
        MODULE, got["strategy"], inputs["identity"].get(got["strategy"]), cfg, started,
        [tabs.verdict_tab(got), tabs.cost_tab(got, cfg), tabs.stress_tab(got),
         tabs.tasks_tab(got), tabs.levels_tab(got, inputs["levels"], cfg)],
        tabs.verdict_block(got), glossary=GLOSSARY, summary=tabs.summary(got))


def run(strategy: str, inputs: dict, cfg: dict) -> dict:
    """Everything the study says about one strategy.

    Args:
        strategy: Its id in the ingest ("17.9.39").
        inputs: What load.load() returned.
        cfg: What config.load() returned.

    Returns:
        The contract dict.
    """
    started = time.time()
    envelope.progress(10, f"leyendo las ocho tareas de {strategy}")
    provenance = {t: inputs["provenance"][f"{t}/{strategy}"] for t in tasks.TASKS
                  if f"{t}/{strategy}" in inputs["provenance"]}
    got = study.one(inputs["keys"], inputs["sims"], inputs["original"], provenance, strategy,
                    cfg)
    envelope.progress(100, "hecho")
    return contract(got, inputs, cfg, started)
