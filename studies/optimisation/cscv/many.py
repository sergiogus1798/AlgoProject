"""Step 18 over one or several mothers' batches: the panels, the one queue, and each mother's facts."""

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from studies.optimisation.cscv.inputs import batch
from studies.optimisation.cscv.inputs.batch import Weekly
from studies.optimisation.cscv.measure import outputs, queue
from studies.optimisation.cscv.measure.queue import Mother, Panel
from studies.optimisation.cscv.verdict import state

FEW = "quedan {n} variantes tras los filtros, menos de {need}: sin dato"
BAND = ("la mediana del PBO del nulo es {got:.2f}, fuera de {low}–{high}: el remuestreo no "
        "está dejando el panel sin nada que elegir; no leas el PBO contra este nulo")
BUDGET = "la cola tardó {got:.0f} s, por encima del presupuesto de {budget:.0f} s"


def panel(metrics: pd.DataFrame, cells: Weekly, cfg: dict) -> Panel:
    """One mother's panel: the variants that enter and their weekly cells.

    Args:
        metrics: Contract C3: `variant_id`, `stratum`, the `param_*` columns.
        cells: `net` and `gross` (weeks x variants), `info` (per variant `trades`, `print`)
            and `years`: what `inputs.batch.read` returned.
        cfg: The study's config.

    Returns:
        `names` (the variants kept), `net` and `gross` (weeks x kept, arrays), `track` (the
        mother's column) and `counts` (`inputs.batch.screen`).
    """
    kept, counts = batch.screen(metrics, cells["info"], cells["years"], cfg["panel"])
    return {"names": np.array(kept), "counts": counts,
            "track": kept.index(counts["madre"]) if counts["madre"] in kept else None,
            "net": cells["net"][kept].to_numpy(np.float64),
            "gross": cells["gross"][kept].to_numpy(np.float64)}


def run(batches: dict[Mother, tuple[pd.DataFrame, Weekly]], cfg: dict,
        progress: Callable[[float], None] | None = None) -> tuple[dict[Mother, dict], dict]:
    """Every mother's CSCV, null and power curve through one queue, and what each says.

    Args:
        batches: Mother -> (its `metrics`, its cells as `inputs.batch.read` returns them).
        cfg: The study's config.
        progress: Called with the share of the queue done.

    Returns:
        (mother -> `facts` (`verdict.state.facts`, or its `no_data`), `counts`, `notes`
        (warnings in Spanish) and, when measured, `names`, `found` (the real run's records),
        `read` (its readings), `draws` and `cpu_s`; the queue's own numbers, `queue.run`).
    """
    panels = {name: panel(metrics, cells, cfg) for name, (metrics, cells) in batches.items()}
    need = cfg["panel"]["min_variants"]
    enough = {name: got for name, got in panels.items() if len(got["names"]) >= need}
    found, perf = queue.run(enough, cfg, progress) if enough else ({}, {})
    tolerance, out = cfg["dominance"]["tolerance"], {}
    for name, got in panels.items():
        notes = list(got["counts"]["avisos"])
        if name not in found:
            out[name] = {"facts": state.no_data(got["counts"]), "counts": got["counts"],
                         "notes": notes + [FEW.format(n=len(got["names"]), need=need)]}
            continue
        ran = found[name]
        read = {"real": outputs.summary(ran["net"], tolerance), "bruto": ran["gross"],
                "seleccion": outputs.selection(ran["net"]["pick"], got["names"]),
                "madre": None if got["track"] is None else outputs.mother(ran["net"], tolerance)}
        facts = state.facts(read, ran["draws"], got["counts"], cfg)
        if not facts["nulo"]["mediana_en_banda"]:
            notes.append(BAND.format(got=facts["nulo"]["pbo_mediana"],
                                     low=cfg["null"]["median_low"],
                                     high=cfg["null"]["median_high"]))
        if perf["wall_s"] > cfg["perf"]["budget_s"]:
            notes.append(BUDGET.format(got=perf["wall_s"], budget=cfg["perf"]["budget_s"]))
        out[name] = {"facts": facts, "counts": got["counts"], "notes": notes,
                     "names": got["names"], "found": ran["net"], "read": read,
                     "draws": ran["draws"], "cpu_s": ran["cpu_s"]}
    return out, perf
