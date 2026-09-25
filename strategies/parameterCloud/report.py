#!/usr/bin/env python3
"""The panel: where the chosen point sits in its own cloud, and whether the cloud holds up."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from strategies.parameterCloud.inputs import cloud as inputs
from strategies.parameterCloud.inputs.config import config
from strategies.parameterCloud.measure import ensemble, stability
from strategies.parameterCloud.model import neighbourhood, sensitivity, space, surrogate
from strategies.parameterCloud.render import text
from strategies.parameterCloud.verdict import call


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
            "reading": reading, "whole": whole, "local": local, "indices": indices,
            "roughness": surrogate.local_roughness(unit, values, s["neighbours"]),
            "curvature": surrogate.curvature(local, unit[origin_row]),
            "window": window, "table": table, "rho": stability.persistence(per, keep),
            "centre": centre, "drift": drift, "pool": pool,
            "blend": ensemble.blend(window["curves"], picked, data["origin"])}


def main() -> None:
    """Read one fabricated batch as a cloud and print what it says about its origin."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="batch directory: metrics.parquet and equity.parquet")
    ap.add_argument("--out", type=Path, help="write every number here as JSON")
    ap.add_argument("--set", dest="overrides", action="append", default=[])
    a = ap.parse_args()

    cfg = config(a.overrides)
    found = read(a.work, cfg)
    verdicts = cfg["verdict"]
    point = call.point(found["reading"], verdicts)
    shape = call.surface(found["local"], found["roughness"], found["curvature"], verdicts)
    over_time = call.temporal(found["table"]["f_y"], found["rho"], found["drift"], verdicts)

    print(text.header(found["data"], found["window"]["cut"], found["collapsed"]))
    print("\n-- A1 · dónde está el punto elegido")
    print(text.point(found["reading"], point))
    print("\n-- A2 y A3 · quién mueve el resultado, y si hay superficie que leer")
    print(text.sensitivity(found["live"], found["indices"], found["local"],
                           found["roughness"], found["curvature"], shape))
    print("\n-- B2 · la superficie, periodo a periodo")
    print(text.stability(found["table"], found["rho"], found["drift"], over_time))
    print("\n-- C1 · la meseta entera contra el punto elegido")
    print(text.ensemble(found["blend"], len(found["pool"])))
    print("\nDiagnóstico, nunca selección: ninguna de estas lecturas sustituye el punto "
          "elegido por un clon mejor. Eso lo decide el dueño, y se revalida aparte.")

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        payload = {"point": point, "surface": shape, "temporal": over_time,
                   "reading": found["reading"], "roughness": found["roughness"],
                   "r2": found["local"]["r2"], "gap": found["blend"]["gap"],
                   "sobol": dict(zip(found["live"], found["indices"]["total"])),
                   "rho_median": float(np.median(found["rho"])),
                   "drift_median": float(np.median(found["drift"])),
                   "periods": json.loads(found["table"].to_json(orient="index"))}
        a.out.write_text(json.dumps(payload, indent=1, default=float), encoding="utf-8")
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
