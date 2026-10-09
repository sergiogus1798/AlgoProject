"""One batch read as a map of who moves the result, returned as the contract's data."""

import time
from pathlib import Path

import pandas as pd

from core.study import blocks, draws, result as envelope
from studies.optimisation.cloud import contract
from studies.optimisation.cloud.inputs import cloud as inputs
from studies.optimisation.cloud.measure import reference
from studies.optimisation.cloud.model import sensitivity, space, surrogate

MODULE = "studies.optimisation.cloud"


def read(frame: pd.DataFrame, cfg: dict, name: str = "") -> dict:
    """The surface, its indices and its shuffled reference on each leg, nothing rendered.

    Args:
        frame: What `inputs.measured` returned.
        cfg: What `config` returned.
        name: The mother's batch name, kept in the recorded draws.

    Returns:
        `cloud` (the variants kept), `counts` (`inputs.screen`), `live` (the parameters
        fitted), `coefficients`, and `legs`: per leg of `inputs.LEGS` the fitted `model`, its
        Sobol `indices` and `r2_adj`, `r2_ref`, `legible`; `draws`, the shuffled references as
        `core.study.draws` rows. `legs` is empty when the cloud has no more variants than the
        surface has coefficients.
    """
    cloud, counts = inputs.screen(frame, cfg["floor_is_per_param"])
    live = space.varying(cloud, [c for c in cloud.columns if c.startswith("param_")])
    found = {"cloud": cloud, "counts": counts, "live": live,
             "coefficients": surrogate.coefficients(len(live)), "legs": {}, "draws": []}
    if len(cloud) <= found["coefficients"]:
        return found
    unit = space.unit(cloud, live)
    for leg in inputs.LEGS:
        y = cloud[f"{leg}_excess"].to_numpy(dtype=float)
        model = surrogate.fit(unit, y)
        shuffled = reference.shuffled(unit, y, cfg["shuffles"], cfg["seed"])
        found["legs"][leg] = {
            "model": model, "indices": sensitivity.sobol(model, cfg["sobol_power"], cfg["seed"]),
            **reference.legible(model["r2_adj"], shuffled, cfg["shuffle_percentile"])}
        found["draws"].append(draws.record(
            "cloud", "r2_barajado", model["r2_adj"], shuffled, strategy=name, seed=cfg["seed"], leg=leg,
            unit="R² ajustado de la superficie con la métrica barajada"))
    return found


def run(work: Path, cfg: dict) -> dict:
    """Which parameters move a mother's excess, and whether that ranking can be read.

    Args:
        work: The batch directory (`inputs.measured`).
        cfg: What `config` returned.

    Returns:
        The contract dict, plus `facts` and `draws` (the report pops it). No verdict on the
        strategy: step 16.5 has no rule.
    """
    started = time.time()
    envelope.progress(5, "valorando las operaciones de build y de oos1")
    frame = inputs.measured(work)
    envelope.progress(60, "superficie, índices de Sobol y referencia barajada")
    found = read(frame, cfg, work.name)
    build = found["legs"].get("build", {})
    result = envelope.envelope(
        MODULE, work.name.replace("_", " ", 1), None, cfg, started, contract.tabs(found, cfg),
        warnings=contract.warnings(found, cfg), glossary=contract.GLOSSARY,
        summary={"variants": len(found["cloud"]), "live": len(found["live"]),
                 "r2_adj": build.get("r2_adj"), "r2_ref": build.get("r2_ref"),
                 "legible": build.get("legible")})
    result["facts"] = blocks.plain(contract.facts(found))
    result["draws"] = found["draws"]
    envelope.progress(100, "hecho")
    return result
