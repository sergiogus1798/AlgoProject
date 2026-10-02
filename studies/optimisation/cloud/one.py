"""One batch read as a cloud around its origin, returned as the contract's data."""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from core.study import result as envelope
from studies.optimisation.cloud import contract
from studies.optimisation.cloud.inputs import cloud as inputs
from studies.optimisation.cloud.measure import ensemble, stability
from studies.optimisation.cloud.model import neighbourhood, sensitivity, space, surrogate
from studies.optimisation.cloud.verdict import call

MODULE = "studies.optimisation.cloud"


def read(work: Path, cfg: dict) -> dict:
    """Every measurement of one batch, with nothing judged and nothing printed.

    Args:
        work: The batch directory, holding contracts C3 and the harvested curves.
        cfg: What `config` returned.

    Returns:
        The cloud, the A1 reading, the surrogate and its indices, the per-period tables
        and the ensemble comparison. `report` renders it; the verdict layer judges it.
    """
    data = inputs.cloud(work, cfg["run"])
    frame, values = data["frame"], inputs.values(data)
    origin_row = int(np.flatnonzero(frame["origin"].to_numpy())[0])
    live = space.varying(frame, data["params"])
    unit = space.unit(frame, live)
    coords = pd.DataFrame(unit, index=frame["variant_id"], columns=live)

    near = neighbourhood.near(space.steps(frame, data["params"]), origin_row,
                              cfg["neighbourhood"]["radius"])
    reading = neighbourhood.reading(values, near, origin_row, cfg["neighbourhood"]["delta"])

    s = cfg["surrogate"]
    whole = surrogate.fit(unit, values)
    local = surrogate.fit(unit[near], values[near])
    indices = sensitivity.sobol(whole, s["sobol_power"], s["seed"])

    harvested = inputs.curves(work, frame["variant_id"])
    window = inputs.before_reserved(harvested, cfg["run"]["symbol"])
    per = stability.periods(window["curves"], cfg["stability"]["period"])
    keep = stability.usable(per, cfg["stability"]["min_active_days"])
    centre, drift = stability.centroids(per, keep, coords, cfg["stability"]["top_share"])
    table = pd.DataFrame({"f_y": stability.fractions(per, keep),
                          "q_origen": stability.origin_rank(per, keep, data["origin"]),
                          "días_activos": per["active"].loc[keep].median(axis=1)})

    pool = ensemble.members(frame, values, near, origin_row, cfg["neighbourhood"]["delta"])
    picked = ensemble.spread(coords, pool, cfg["ensemble"]["k"])

    return {"data": data, "live": live, "collapsed": sorted(set(data["params"]) - set(live)),
            "reading": reading, "values": values, "near_mask": near,
            "whole": whole, "local": local, "indices": indices,
            "roughness": surrogate.local_roughness(unit, values, s["neighbours"]),
            "curvature": surrogate.curvature(local, unit[origin_row]),
            "window": window, "table": table, "rho": stability.persistence(per, keep),
            "centre": centre, "drift": drift, "pool": pool,
            "blend": ensemble.blend(window["curves"], picked, data["origin"])}


def run(work: Path, cfg: dict) -> dict:
    """Where the chosen point sits in its own cloud, and whether the cloud holds up.

    Args:
        work: The batch directory, holding contracts C3 and the harvested curves.
        cfg: What `config` returned.

    Returns:
        The contract dict: four tabs, each with its readings. No verdict on the strategy:
        diagnosis, never selection — nothing here replaces the chosen point by a better
        clone; that is the owner's decision, revalidated elsewhere.
    """
    started = time.time()
    found = read(work, cfg)
    v = cfg["verdict"]
    calls = {"point": call.point(found["reading"], v),
             "surface": call.surface(found["local"], found["roughness"], found["curvature"], v),
             "temporal": call.temporal(found["table"]["f_y"], found["rho"], found["drift"], v)}
    data = found["data"]
    warn = []
    if found["collapsed"]:
        warn.append({"code": "colapsados", "state": "watch",
                     "text": "Colapsados por los filtros, fuera del modelo: "
                             + ", ".join(c[6:] for c in found["collapsed"])
                             + ". Un parámetro así elige entre operar y no operar."})
    if found["window"]["cut"]:
        warn.append({"code": "reservado", "state": "info",
                     "text": f"{found['window']['cut']} días recortados: caen en el tramo "
                             f"reservado oos2."})
    return envelope.envelope(
        MODULE, data["origin"], None, cfg, started, contract.tabs(found, calls),
        warnings=warn, glossary=contract.GLOSSARY,
        summary={"point": calls["point"], "surface": calls["surface"],
                 "temporal": calls["temporal"], "variants": len(data["frame"]),
                 "dropped": data["dropped"], "r2": found["local"]["r2"],
                 "gap": found["blend"]["gap"],
                 "rho_median": float(np.median(found["rho"])),
                 "drift_median": float(np.median(found["drift"])),
                 "sobol": dict(zip(found["live"], found["indices"]["total"])),
                 "reading": found["reading"], "roughness": found["roughness"],
                 "periods": json.loads(found["table"].to_json(orient="index"))})
