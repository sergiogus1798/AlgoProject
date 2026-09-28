"""One strategy's profit shape, returned as the contract's data: what the window paints."""

import time
from pathlib import Path

import numpy as np

from core.study import identity, output, result as envelope
from studies.readings.profitShape import breaks, concentration, contract, dependence, inputs

MODULE = "studies.readings.profitShape"
GLOSSARY = [
    {"term": "Concentración", "text": "Qué parte del beneficio total ponen las mejores "
     "operaciones o los mejores meses."},
    {"term": "Rachas (Wald-Wolfowitz)", "text": "Cuántas veces cambia el signo de una "
     "operación a la siguiente, contra lo que daría el azar. Menos cambios de los esperados "
     "(z negativo) es agrupamiento."},
    {"term": "Ljung-Box", "text": "Si el tamaño de una operación o de un día predice el del "
     "siguiente."},
    {"term": "CUSUM", "text": "La suma acumulada de desviaciones respecto a la media; si se "
     "aleja demasiado, la media cambió dentro de la muestra."}]


def read(packed: Path, strategy: str, cfg: dict) -> dict:
    """Every measurement for one strategy, with nothing judged.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        cfg: What `inputs.config` returned.

    Returns:
        The three families of numbers, keyed `concentration`, `dependence` and `breaks`.
    """
    run, dep, brk = cfg["run"], cfg["dependence"], cfg["breaks"]
    data = inputs.stream(packed, strategy, run["sample"])
    pnl, wins = data["pnl"], data["wins"]
    conc = concentration.time_concentration(data["trades"], pnl, run["best_months"])
    conc.update({"top1": concentration.top_share(pnl, 0.01),
                 "top5": concentration.top_share(pnl, 0.05),
                 "mean": float(pnl.mean()), "median": float(np.median(pnl)),
                 "trimmed": concentration.trimmed(pnl, run["trim"])})
    dependent = {"runs": dependence.runs(wins),
                 "trades": dependence.ljung_box(pnl, dep["lags"]),
                 "daily": dependence.ljung_box(data["daily"].to_numpy(), dep["lags"]),
                 "streak": dependence.streak(wins, dep["draws"], dep["seed"])}
    found = breaks.cusum(pnl) if pnl.size >= brk["min_trades"] else None
    structure = {"cusum": found, "n": pnl.size}
    if found:
        structure["sides"] = breaks.either_side(pnl, found["at"])
        structure["rolling"] = breaks.rolling(pnl, brk["window"])
        structure["date"] = data["trades"].loc[found["at"], "Open time"]
    return {"data": data, "concentration": conc, "dependence": dependent,
            "breaks": structure}


def run(strategy: str, export: Path, cfg: dict) -> dict:
    """What few things one strategy's result rests on.

    Args:
        strategy: Its name exactly as the export spells it.
        export: The `trades.parquet` an export wrote.
        cfg: What `inputs.config` returned.

    Returns:
        The contract dict: three tabs, each with its reading, and no overall verdict — this
        study describes; a filter taken from it is a new search and is logged as one.
    """
    started = time.time()
    found = read(export, strategy, cfg)
    ident = output.identify(export.parent, [strategy])[strategy]
    return envelope.envelope(
        MODULE, strategy, ident, cfg, started,
        [contract.concentration_tab(found["concentration"], cfg),
         contract.dependence_tab(found["dependence"], cfg), contract.breaks_tab(found["breaks"])],
        warnings=[{"code": "descriptivo", "state": "info",
                   "text": "Con siete diagnósticos alguno falla por azar incluso en una "
                           "estrategia buena. Un filtro sacado de aquí es una búsqueda nueva "
                           "y se anota en el ledger."}] + identity.warning(ident),
        glossary=GLOSSARY,
        summary={"trades": int(found["data"]["pnl"].size), "sample": cfg["run"]["sample"]})
