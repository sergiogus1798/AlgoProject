"""One strategy's Monte Carlo Retest, returned as the contract's data: what the window paints."""

import time

from core.study import draws, result as envelope
from studies.breakage.mcRetest import run as study
from studies.breakage.mcRetest.contract import retention, tabs
from studies.breakage.mcRetest.inputs import tasks

MODULE = "studies.breakage.mcRetest"
GLOSSARY = [
    {"term": "Control", "text": "La tarea que sólo cambia la barra de inicio. Lo que mueve es "
     "ruido irreducible, y todo coste se mide en múltiplos de su dispersión."},
    {"term": "CVaR del drawdown", "text": "La media del 5 % de peores drawdowns, no su "
     "percentil: lo que pasa cuando pasa lo malo."},
    {"term": "Rejilla", "text": "Una tarea cuyas mil simulaciones dan pocos valores distintos: "
     "sin forma que medir, sólo extremos."},
    {"term": "Bimodal", "text": "Dos grupos de resultados separados: la perturbación a veces "
     "rompe la estrategia y a veces no la toca."},
    {"term": "Estrés combinado", "text": "La tarea que perturba las seis cosas a la vez (barra, "
     "spread, slippage, parámetros, salidas e histórico) sobre la muestra completa."},
    {"term": "Re-ejecución", "text": "Una de las simulaciones de SQX: el mismo backtest con la "
     "perturbación sorteada de nuevo."},
    {"term": "Net Profit p5", "text": "El percentil 5 del Net Profit: el 5 % de las re-ejecuciones "
     "gana menos que esto. Es el listón de lo que se sostiene con mala suerte."},
    {"term": "Mediana Monte Carlo", "text": "El Net Profit central de las re-ejecuciones. Si "
     "queda muy lejos del backtest original, el resultado original era un caso extremo."},
    {"term": "Banda de percentiles", "text": "La banda clara contiene del 5 al 95 % de las curvas "
     "de equity simuladas y la oscura del 25 al 75 %; la línea central es la mediana."},
    {"term": "Sigma", "text": "Desviación típica; aquí, la del control. Un coste en sigmas dice "
     "cuántas veces el ruido irreducible mueve la perturbación."},
    {"term": "Veto", "text": "Una comprobación que descalifica a la estrategia por sí sola; el "
     "aviso, en cambio, solo la marca."},
    {"term": "Simulaciones rentables", "text": "El porcentaje de re-ejecuciones con Net Profit "
     "mayor que cero."}]


def contract(got: dict, inputs: dict, cfg: dict, started: float) -> dict:
    """What run.one() concluded, as the contract dict.

    Args:
        got: What run.one() returned for one strategy.
        inputs: What load.load() returned.
        cfg: What config.load() returned.
        started: When the computation began.

    Returns:
        Verdict, the tabs of what ran, glossary and the summary row, and `draws`: each task's
        re-executions as `core.study.draws` rows (the report pops it before writing). `inputs["t1"]`, when
        something put it there, is {strategy: T1 facts} for `retention.tab`.
    """
    t1 = (inputs.get("t1") or {}).get(got["strategy"])
    made = [tabs.verdict_tab(got), retention.tab(t1), tabs.cost_tab(got, cfg),
            tabs.stress_tab(got), tabs.tasks_tab(got), tabs.levels_tab(got, inputs["levels"], cfg)]
    identity = inputs["identity"].get(got["strategy"])
    kept = [draws.record("mcRetest", "net_p5", got[t]["original_net"], got[t]["_net"],
                         identity or "", strategy=got["strategy"], seed=None, task=t,
                         unit="Net Profit de las re-ejecuciones de SQX, USD")
            for t in tasks.TASKS if t in got]
    return envelope.envelope(
        MODULE, got["strategy"], identity, cfg, started,
        [t for t in made if t], tabs.verdict_block(got),
        warnings=tabs.sparse_warnings(got), glossary=GLOSSARY,
        summary=tabs.summary(got)) | {"draws": kept}


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
    envelope.progress(10, f"leyendo las tareas de {strategy}")
    provenance = {t: inputs["provenance"][f"{t}/{strategy}"] for t in tasks.TASKS
                  if f"{t}/{strategy}" in inputs["provenance"]}
    bench = study.benchmarks(inputs["trades"], inputs["asset"]).get(strategy, 0.0)
    got = study.one(inputs["keys"], inputs["sims"], inputs["original"], provenance, strategy,
                    bench, cfg)
    envelope.progress(100, "hecho")
    return contract(got, inputs, cfg, started)
