"""Every strategy of one export against buy and hold, and the population read as one result."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.closing.exposure import one


def run(inputs: dict, cfg: dict) -> dict:
    """Every strategy measured and judged.

    Args:
        inputs: What load.load() returned.
        cfg: What `inputs.config` returned.

    Returns:
        {"population": the export's result, "table": one row per strategy with its
        identity and verdict, "members": one result per strategy}.
    """
    started = time.time()
    members = []
    for i, name in enumerate(inputs["strategies"], 1):
        members.append(one.run(name, inputs, cfg))
        envelope.progress(100 * i // len(inputs["strategies"]),
                          f"{name}: {members[-1]['summary']['verdict']}")
    table = pd.DataFrame([{"strategy": m["strategy"], "identity": m["identity"],
                           **m["summary"]} for m in members])
    table = table[["strategy", "identity", "verdict"]
                  + [c for c in table.columns if c not in ("strategy", "identity", "verdict")]]
    worth = int((table.verdict == "worth_it").sum())
    shown = table[["strategy", "verdict", "n", "exp_share", "exp_hours_per_week",
                   "strat_return_pct", "return_per_exposure_pct", "efficiency",
                   "return_ratio", "dd_ratio", "reasons"]]
    population = envelope.envelope(
        one.MODULE, None, None, cfg, started,
        [envelope.tab("summary", "Rendimiento contra exposición", [
            {"kind": "bars", "title": "Eficiencia por hora expuesta, frente al buy and hold",
             "unit": "×", "reference": cfg["gate"]["min_efficiency"],
             "items": [{"label": r.strategy, "value": r.efficiency, "error": None,
                        "state": "pass" if r.verdict == "worth_it" else "fail"}
                       for r in table.itertuples()]},
            blocks.table("Estrategia a estrategia", shown)])],
        blocks.verdict(f"{worth} de {len(table)}", "pass" if worth else "fail",
                       f"{worth} estrategias rinden por hora expuesta al menos "
                       f"{cfg['gate']['min_efficiency']:.1f} veces lo que el buy and hold."))
    return {"population": population, "table": table, "members": members}
