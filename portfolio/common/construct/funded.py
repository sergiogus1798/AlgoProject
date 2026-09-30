"""THE COMMAND: build a funded portfolio -- universe, sizing, pair screen, greedy seeds + GA."""

import argparse
import json
import resource
import time
from datetime import datetime, timezone as tz
from pathlib import Path

import numpy as np
import pandas as pd

from core.archive import read as archive_read
from core.datapaths import portfolio_dir
from portfolio.funded.rules import catalog

from .equity import universe
from .inputs import config, pool as pool_mod, risk
from portfolio.common.construct.search import admissible, genetic, greedy, stagea, stagea_data, trials

RUNS = portfolio_dir() / "runs"


def _member_meta(identity: str) -> dict:
    """symbol, timeframe and family off the member's own archived manifest."""
    version = archive_read.versions(identity)[-1]
    row = archive_read.load(identity, version)["manifest"]["registry"]
    return {"symbol": row["symbol"], "timeframe": row["timeframe"],
            "family": Path(row["template"]).parent.name}


def size_members(kept: list[str]) -> tuple[dict, list[tuple[str, str]]]:
    """Every kept member's fixed-risk factor; names those with no step-24 stop.

    Args:
        kept: Identities the universe kept (reconciled, licensed).

    Returns:
        `factors` (identity -> `inputs.risk.sizing()`), `excluded` (identity, reason) pairs.
    """
    factors, excluded = {}, []
    for identity in kept:
        version = archive_read.versions(identity)[-1]
        try:
            factors[identity] = risk.sizing(identity, version)
        except ValueError as exc:
            excluded.append((identity, str(exc)))
    return factors, excluded


def build(pool_name: str, plan_key: str, cfg: dict) -> dict:
    """Run the whole funded search: universe, sizing, pair screen, greedy seeds + GA.

    Args:
        pool_name: A declared pool (`inputs.pool.declare`).
        plan_key: A funded plan, as `portfolio.funded.rules.catalog.plans` lists it.
        cfg: `inputs.config.load()`'s result.

    Returns:
        `usable`, `excluded_stop`, `graph` (admissible.admissible's dict), `identities`
        (graph order, `usable` members only), `run` (genetic.run's result, with `level`
        added), `plan`, `members_meta`, `pool`, `wall_s`, `peak_mb`, `root_seed`. `run` is
        `None` when no member is usable.
    """
    start = time.perf_counter()
    rng = np.random.default_rng()
    root_seed = int(rng.integers(0, 2**63 - 1))
    rng = np.random.default_rng(root_seed)

    plan = catalog.plan(plan_key)
    out_dir = universe.build(pool_name, cfg)
    data = universe.load(out_dir)
    kept = data["manifest"]["members"]["kept"]

    factors, excluded_stop = size_members(kept)
    usable = [i for i in kept if i in factors]
    result = {"pool_name": pool_name, "plan_key": plan_key, "plan": plan, "kept": kept,
              "excluded_stop": excluded_stop, "usable": usable, "run": None}
    if not usable:
        result["wall_s"] = time.perf_counter() - start
        result["peak_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        return result

    daily = data["daily"][usable]
    calendar = {k: (pd.Timestamp(v[0]), pd.Timestamp(v[1]))
                for k, v in data["manifest"]["calendar"].items()}
    from .equity import matrix
    from .pairs import table
    build_daily = matrix.segment(daily, calendar, "build")
    pairs = table.table(build_daily, matrix.segment(data["monthly"][usable], calendar, "build"), cfg)
    got = admissible.admissible(pairs, usable, cfg)
    identities = usable

    members_meta = {i: _member_meta(i) for i in identities}
    min_size = {i: factors[i]["min_size"] for i in identities}
    fc = {i: factors[i]["factor"] for i in identities}
    prepared = stagea_data.prepare(data, plan["firm"], identities, data["manifest"]["calendar"],
                                    fc, min_size)

    levels_log: list[np.ndarray] = []

    def score(combos: np.ndarray) -> np.ndarray:
        """One generation's best P(pass) per combination, over the risk grid; logs the chosen level."""
        scored = stagea.evaluate(prepared, combos, plan, cfg)
        best_p, best_r = stagea.best(scored, cfg["funded"]["risk_grid"])
        levels_log.append(best_r)
        return best_p

    seeds = greedy.seeds(got["graph"], cfg["search"]["seeds"], rng)
    run = genetic.run(got["graph"], score, seeds, cfg["search"]["ga"], rng)
    run["level"] = np.concatenate(levels_log) if levels_log else np.full(run["score"].shape, np.nan)

    result.update(graph=got, identities=identities, run=run, members_meta=members_meta,
                  root_seed=root_seed)
    result["wall_s"] = time.perf_counter() - start
    result["peak_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    return result


def write_run(result: dict) -> Path:
    """Write `search.parquet` and `manifest.json` under `RUNS/<stamp>_<pool>_<plan>/`."""
    identities = result["identities"]
    run = result["run"]
    stamp = datetime.now(tz.utc).strftime("%Y-%m-%dT%H%M")
    safe_plan = result["plan_key"].replace(":", "_")
    out = RUNS / f"{stamp}_{result['pool_name']}_{safe_plan}"
    out.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame({
        "members": ["+".join(identities[i] for i in np.sort(m)) for m in run["members"]],
        "score": run["score"], "level": run["level"], "origin": run["origin"],
        "generation": run["generation"],
    })
    frame.to_parquet(out / "search.parquet")
    manifest = {"pool": result["pool_name"], "plan": result["plan_key"],
                "root_seed": result["root_seed"], "n_scored": len(frame),
                "best_members": [identities[i] for i in run["best"]["members"]],
                "best_score": run["best"]["score"], "wall_s": result["wall_s"],
                "peak_mb": result["peak_mb"], "generations_run": run["generations_run"],
                "overhead_s": run["overhead_s"], "score_s": run["score_s"]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return out


def summarise(result: dict, out: Path | None) -> str:
    """The Spanish report the owner reads: excluded members, best combinations, cost."""
    lines = [f"Pool '{result['pool_name']}' plan {result['plan_key']}: "
             f"{len(result['kept'])} miembros en el universo"]
    for identity, reason in result["excluded_stop"]:
        lines.append(f"  excluida {identity[:12]}…: {reason}")
    if result["run"] is None:
        lines.append("Ningun miembro utilizable: no hay stop del paso 24 en ninguno.")
        print(text := "\n".join(lines))
        return text
    run = result["run"]
    identities = result["identities"]
    frame = pd.DataFrame({"members": run["members"], "score": run["score"], "level": run["level"]})
    frame = frame.assign(key=frame["members"].map(lambda m: tuple(sorted(m.tolist()))))
    top = frame.sort_values("score", ascending=False).drop_duplicates("key").head(10)
    lines.append(f"Búsqueda: {len(run['score'])} combinaciones evaluadas en "
                 f"{run['generations_run']} generaciones")
    for row in top.itertuples():
        names = ", ".join(identities[i][:8] for i in row.key)
        lines.append(f"  K={len(row.key)} P(pass)={row.score:.3f} r={row.level:.3%} [{names}]")
    lines.append(f"Tiempo: {result['wall_s']:.1f} s (GA propio ~{run['overhead_s']/run['generations_run']*1000:.1f} "
                 f"ms/generación, evaluación {run['score_s']:.1f} s) · RAM pico: {result['peak_mb']:.0f} MB")
    if result["plan"]["flags"]:
        lines.append(f"Reglas sin confirmar: {[f['rule_key'] for f in result['plan']['flags']]}")
    if out is not None:
        lines.append(f"Carpeta: {out}")
    text = "\n".join(lines)
    print(text)
    return text


def main() -> None:
    """Search a funded portfolio for one pool and plan; ledger rows, Spanish summary."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()

    cfg = config.load(args.overrides)
    result = build(args.pool, args.plan, cfg)
    if result["run"] is None:
        summarise(result, None)
        return
    out = write_run(result)
    trials.record(result["run"], pool_mod.read(args.pool, cfg.get("pool", {}).get("firm")),
                  args.plan, result["members_meta"], cfg)
    summarise(result, out)


if __name__ == "__main__":
    main()
