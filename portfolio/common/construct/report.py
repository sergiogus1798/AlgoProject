"""THE COMMAND: a pool's portfolio by ranks and its verdict (M5) -- search, oos1, oos2 once, hand-off."""

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from core.study import output

from . import handoff, many, real, weights
from .inputs import config
from .inputs import pool as pool_mod
from .search import trials_real

TITLE = "Cartera por rangos: la elección en build y su veredicto"


def load(pool_name: str, cfg: dict, run: Path | None, seed: int) -> dict[str, Any]:
    """What the verdict reads: a run of `real.py` (made now when `run` is None) and its world.

    Returns:
        `result` (`real.build()`'s), `members` (the run's chosen identities), `pool` (the
        declared pool), `table` (`search.parquet`), `run` (the folder); `run` None when no
        member of the pool is usable.
    """
    result = real.build(pool_name, cfg, seed, search=run is None)
    pool = pool_mod.declared(pool_name, cfg)
    if "unit" not in result:
        return {"result": result, "run": None}
    if run is None:
        table = real.frame(result)
        run = real.write_run(result, table)
        trials_real.record(result["found"], pool, result["members_meta"],
                           f"{result['found']['mode']}; relaxed={cfg['relaxed'] or 'no'}")
        print(real.summarise(result, table, run).replace(
            "Sin veredicto: es la elección en build; el juicio en oos1 y oos2 es el hito M5.\n", ""))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    if manifest["pool"] != pool_name:
        raise SystemExit(f"{run.name} es una run del pool '{manifest['pool']}', no de '{pool_name}'")
    missing = [m for m in manifest["best_members"] if m not in result["identities"]]
    if missing:
        raise SystemExit(f"la cartera de {run.name} tiene miembros que este pool no da por "
                         f"utilizables con esta configuración: {[m[:12] for m in missing]}")
    return {"result": result, "members": manifest["best_members"], "pool": pool, "run": run,
            "table": pd.read_parquet(run / "search.parquet")}


def write(inputs: dict, got: dict, cfg: dict) -> None:
    """`verdict.json`, the manifest's `verdict`, the contract result and the hand-off, in the run folder."""
    run, v = inputs["run"], got["verdict"]
    kept = {**v, **({"oos1": {k: x for k, x in v["oos1"].items() if k != "scores"}} if "oos1" in v else {})}
    (run / "verdict.json").write_text(json.dumps(
        {**kept, "sentence": got["sentence"], "root_seed": got["root_seed"], "relaxed": cfg["relaxed"]},
        indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    manifest["verdict"] = {"label": v["label"], "pass": v["pass"]}
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2, default=float), encoding="utf-8")
    output.population(run, "cartera", got["population"], TITLE, got["sentence"])
    r, members = inputs["result"], inputs["members"]
    held = weights.matrix(r["daily"], many.mask(inputs), cfg)[0]
    handoff.write(run, r["pool_name"], inputs["pool"], members,
                  {i: float(w) for i, w in zip(r["identities"], held) if w > 0},
                  r["daily"], r["calendar"], v, got["sentence"], cfg)


def main() -> None:
    """Choose (or take) a pool's portfolio, judge it, write the result and print the decision."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", required=True)
    parser.add_argument("--firm", help="empresa cuyas prohibiciones se quitan del pool")
    parser.add_argument("--run", type=Path, help="carpeta de una run de real.py: juzga su "
                                                 "cartera sin buscar otra vez")
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    parser.add_argument("--seed", type=int, required=True, help="semilla de los sorteos; queda en lo que se escribe")
    args = parser.parse_args()
    cfg = pool_mod.scoped(config.load(args.overrides), args.firm)
    for key, allowed in real.REQUIRED.items():
        if cfg["real"][key] not in allowed:
            raise SystemExit(f"real.{key} no tiene valor y no lleva defecto: --set real.{key}="
                             f"{'|'.join(allowed)}")
    inputs = load(args.pool, cfg, args.run, args.seed)
    if inputs["run"] is None:
        print(real.summarise(inputs["result"], None, None))
        return
    got = many.run(inputs, cfg, args.seed)
    write(inputs, got, cfg)
    if cfg["relaxed"]:
        print(f"AJUSTADO: umbrales relajados {cfg['relaxed']} — no es un resultado")
    print(got["sentence"])
    print(f"Carpeta: {inputs['run']} (verdict.json, cartera.html, handoff/)")


if __name__ == "__main__":
    main()
