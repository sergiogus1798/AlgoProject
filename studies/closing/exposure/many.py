"""Every strategy of one export against buy & hold, and the population read as one result."""

import time
from typing import Any, TypedDict

import pandas as pd

from core import fanout
from core.study import blocks, result as envelope
from studies.closing.exposure import one
from studies.closing.exposure.load import Loaded

SHOWN = {"strategy": "Estrategia", "n": "Operaciones",
         "exp_share": "Barras con posición (%)", "exp_hours_per_week": "Horas por semana",
         "strat_return_pct": "Retorno (%)", "return_per_exposure_pct": "Rendimiento por hora expuesta (%)",
         "efficiency": "Eficiencia", "return_ratio": "Retorno frente al buy & hold",
         "dd_ratio": "Drawdown frente al buy & hold", "notes": "Avisos"}

# What verdict.csv carries, hence the Databanks columns of «Exposición»: the rest of the flat
# row (44 figures) stays in each strategy's own result.
CSV = ["strategy", "identity", "n", "exp_share", "exp_hours_per_week",
       "strat_return_pct", "return_per_exposure_pct", "efficiency", "return_ratio", "dd_ratio",
       "captured", "aligned", "notes"]


_SHARED: dict = {}     # set by `run` before the fork, read by `_member` in the workers


def _member(name: str) -> dict:
    """One strategy measured, in a worker that inherited the export's trades."""
    return one.run(name, _SHARED["inputs"], _SHARED["cfg"])


class Measured(TypedDict):
    """The population's result, one row per strategy, and each strategy's own result."""

    population: dict[str, Any]
    table: pd.DataFrame
    members: list[dict[str, Any]]


def run(inputs: Loaded, cfg: dict) -> Measured:
    """Every strategy measured; none is judged.

    Args:
        inputs: What load.load() returned.
        cfg: What `inputs.config` returned.

    Returns:
        {"population": the export's result, "table": one row per strategy with its
        identity, "members": one result per strategy}.
    """
    started = time.time()
    names = inputs["strategies"]
    _SHARED.update(inputs=inputs, cfg=cfg)
    done = {}
    for name, member in fanout.run(_member, {n: 1 for n in names}, fanout.CORES):
        done[name] = member
        envelope.progress(100 * len(done) // len(names), f"{name}: {member['summary']['n']} operaciones")
    members = [done[n] for n in names]
    table = pd.DataFrame([{"strategy": m["strategy"], "identity": m["identity"],
                           **m["summary"]} for m in members])
    shown = table[["strategy", "n", "exp_share", "exp_hours_per_week",
                   "strat_return_pct", "return_per_exposure_pct", "efficiency",
                   "return_ratio", "dd_ratio", "notes"]].assign(
        exp_share=table["exp_share"] * 100).rename(
        columns=SHOWN)
    population = envelope.envelope(
        one.MODULE, None, None, cfg, started,
        [envelope.tab("summary", "Rendimiento contra exposición", [
            {"kind": "bars", "title": "Eficiencia por hora expuesta, frente al buy & hold",
             "unit": "×", "reference": 1.0,
             "items": [{"label": label, "value": value, "error": None,
                        "state": "none"}
                       for label, value in zip(table["strategy"], table["efficiency"], strict=True)]},
            blocks.table("Estrategia a estrategia", shown, "Tiempo en el mercado en %; rendimientos en %.")])],
        None)
    return {"population": population, "table": table, "members": members}
