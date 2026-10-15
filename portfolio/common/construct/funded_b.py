"""THE COMMAND: stage B and the funded verdict on an existing stage-A run."""

import argparse
import json
import resource
import shutil
import time
from pathlib import Path
from typing import Any

import numba
import numpy as np
import pandas as pd

from core import fanout
from core.barstore import source as bars_of
from portfolio.funded.rules import catalog

from . import funded, funded_verdict, handoff
from .equity import universe
from .funded_verdict import prepare as _prepare
from .funded_verdict import union as _union
from .inputs import config, source
from .inputs import pool as pool_mod
from .pairs import table as pairs_table
from .search import (
    admissible,
    shortlist,
    stagea,
    stagea_data,
    stageb,
    stageb_null,
    stageb_run,
    trials,
)
from .verdict import decide

REQUIRED = {"shared_of": ("smaller", "larger"), "t1_gap": ("close_to_open_blocks",)}
OWN = ("stageb.", "verdict.")  # knobs that never change the universe a run is read from
WRITES = ("shortlist.parquet", "stageb.parquet", "verdict.json", "verdict_rows.parquet")


def refuse_unset(cfg: dict) -> None:
    """Stop when a knob with more than one reading was left empty (root CLAUDE.md, rule 11)."""
    funded.refuse_uncapped(cfg)
    for key, allowed in REQUIRED.items():
        if cfg["stageb"][key] not in allowed:
            raise SystemExit(
                f"stageb.{key} no está fijado: elige entre {list(allowed)} con "
                f"--set stageb.{key}=<valor>; no hay valor por defecto."
            )


def load(run: Path, overrides: list[str]) -> dict[str, Any]:
    """Everything a stage-A run's folder points at, read from the archive and the universe.

    Returns:
        The world `build()` reads: `pool_name`, `plan`, `search` (`search.parquet`),
        `universe` (`equity.store.load()`), `firm`, `calendar`, `identities` and `graph` (the
        admissible graph over the members with a step-24 stop), `sources`, `bars` (per feed),
        `factors`, `min_size`, `meta` (identity -> symbol, timeframe, family),
        `clock_unconfirmed` (the firm's clock is flagged in `config.yaml`), `base` (the config
        the universe is read under, scoped to the run's `--firm`), `pool` (the declared pool).
    """
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    plan = catalog.plan(manifest["plan"])
    base = pool_mod.scoped(
        config.load([o for o in overrides if not o.startswith(OWN)]),
        manifest.get("firm"),
        manifest["plan"],
    )  # the run's own prohibitions
    data = universe.load(universe.build(manifest["pool"], base))
    versions = funded.frozen_versions(manifest["pool"], base)
    sized, _ = funded.size_members(data["manifest"]["members"]["kept"], versions)
    identities = list(sized)
    calendar = {
        k: (pd.Timestamp(v[0]), pd.Timestamp(v[1]))
        for k, v in data["manifest"]["calendar"].items()
    }
    lo, hi = calendar["build"]
    build = data["daily"][identities].loc[lo:hi]  # months summed from build's own days
    pairs = pairs_table.table(
        build, build.groupby(build.index.to_period("M")).sum(min_count=1), base
    )
    sources = {i: source.load(i, versions[i]) for i in identities}
    feeds = sorted({s["feed"] for s in sources.values()})
    return {
        "pool_name": manifest["pool"],
        "plan": plan,
        "base": base,
        "pool": pool_mod.declared(manifest["pool"], base),
        "search": pd.read_parquet(run / "search.parquet"),
        "universe": data,
        "firm": plan["firm"],
        "calendar": calendar,
        "identities": identities,
        "clock_unconfirmed": plan["firm"] in base["equity"]["unconfirmed_clocks"],
        "graph": admissible.admissible(pairs, identities, base)["graph"],
        "sources": sources,
        "bars": {f: bars_of(f, ["High", "Low", "Close"]) for f in feeds},
        "factors": {i: s["factor"] for i, s in sized.items()},
        "min_size": {i: s["min_size"] for i, s in sized.items()},
        "meta": {i: funded._member_meta(i, versions) for i in identities},
    }


def _null_shortlists(
    world: dict, cfg: dict, rng: np.random.Generator
) -> tuple[list, int]:
    """The null searches' shortlists: random admissible combinations scored by stage A."""
    prepared = stagea_data.prepare(
        world["universe"],
        world["firm"],
        world["identities"],
        world["calendar"],
        world["factors"],
        world["min_size"],
    )
    sizes = (world["search"]["members"].str.count(r"\+") + 1).to_numpy()
    n = cfg["verdict"]["null_candidates"] or len(world["search"])

    def score(combos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Stage A's objective: each row's best P(pass) over the risk grid, and that level."""
        return stagea.best(
            stagea.evaluate(prepared, combos, world["plan"], cfg),
            cfg["funded"]["risk_grid"],
        )

    return [
        stageb_null.shortlisted(
            score, world["graph"], world["identities"], sizes, n, cfg, rng
        )
        for _ in range(cfg["verdict"]["null_draws"])
    ], n


def build(world: dict, cfg: dict, rng: np.random.Generator) -> dict[str, Any]:
    """Stage B on the run's shortlist, then the verdict when oos1 exists (`funded_verdict.judge`).

    Returns:
        `stage_b` (`stageb_run.run()`; its `winner` gains `p_fresh`, the P(pass) to report: the
        stability re-draws' mean, where `p` is the selector's), `stability`, `ranking_n`
        (distinct combinations of the search), `verdict` (`verdict.decide.verdict()`, or None
        with `reason`), `nulls` (each null search's winner and measures), `segments` (the
        judging segments the pool has days in).
    """
    refuse_unset(cfg)
    numba.set_num_threads(min(fanout.CORES, numba.config.NUMBA_NUM_THREADS))  # pyright: ignore[reportPrivateImportUsage, reportAttributeAccessIssue]  # numba stubs omit config.NUMBA_NUM_THREADS
    plan = world["plan"]
    ranking = shortlist.ranked(world["search"])
    sb = cfg["stageb"]
    short = shortlist.diverse(
        ranking, sb["shortlist_size"], sb["max_shared"], sb["shared_of"]
    )
    segments = funded_verdict.segments(world)
    out = {
        "ranking_n": len(ranking),
        "segments": segments,
        "verdict": None,
        "nulls": [],
    }
    judging = "oos1" in segments
    nulls, n_candidates = _null_shortlists(world, cfg, rng) if judging else ([], 0)

    data = _prepare(world, _union([short, *nulls]), world["calendar"]["build"], cfg)
    out["stage_b"] = b = stageb_run.run(short, data, plan, cfg, rng)
    winner = b["winner"]
    out["stability"] = stageb.stability(
        data,
        stageb_run.rows_of(data, winner["members"]),
        plan,
        cfg,
        stageb_run.risk_of(winner, plan),
        rng.spawn(1)[0],
    )
    # `p` chose the winner — the best of shortlist × risks noisy figures, so it reads high; what
    # is reported is the same figure on fresh paths from an independent seed
    winner["p_fresh"] = out["stability"]["mean"]
    if not judging:
        out["reason"] = (
            "sin oos1 en el universo: el veredicto empieza por oos1 y no se emite"
        )
        return out
    null_winners = [stageb_run.run(n, data, plan, cfg, rng)["winner"] for n in nulls]
    out.update(
        funded_verdict.judge(world, cfg, rng, b, len(short), null_winners, n_candidates)
    )
    return out


def target(run: Path) -> Path:
    """Where this stage B writes: the stage-A run's folder, or a new run when that one holds a stage B.

    Returns:
        `run` the first time. When it already has a stage B (`stageb.parquet` or
        `verdict.json`), a new run folder named as stage A names one, holding a copy of the
        stage-A files and `stage_a_run` in its manifest — so a rerun never writes over an
        earlier stage B, its verdict or its hand-off (OPEN #104-4).
    """
    if not any((run / name).exists() for name in WRITES):
        return run
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    out = funded.new_run(manifest["pool"], manifest["plan"])
    for file in run.iterdir():
        if file.is_file() and file.name not in WRITES:
            shutil.copy2(file, out / file.name)
    manifest["stage_a_run"] = manifest.get("stage_a_run", run.name)
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
    return out


def write(run: Path, result: dict, extra: dict) -> None:
    """`shortlist.parquet`, `stageb.parquet` and `verdict.json`, next to the stage-A run's files."""
    b = result["stage_b"]
    b["table"].to_parquet(run / "shortlist.parquet")
    b["rows"].to_parquet(run / "stageb.parquet")
    judged = result.get("judged")
    blob = {
        "winner": b["winner"],
        "stability": result["stability"],
        "segments": result["segments"],
        "verdict": result["verdict"],
        "reason": result.get("reason"),
        "nulls": result["nulls"],
        "judged": None
        if judged is None
        else {k: v for k, v in judged.items() if k != "rows"},
        **extra,
    }
    (run / "verdict.json").write_text(
        json.dumps(
            blob, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)
        ),
        encoding="utf-8",
    )
    if judged is not None:
        judged["rows"].to_parquet(run / "verdict_rows.parquet")
    # the seed beside the stage-A one, in the manifest the run folder is read by (OPEN #104-3)
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    manifest["stage_b_seed"] = extra["root_seed"]
    (run / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )


def summarise(world: dict, result: dict) -> str:
    """The Spanish report: the shortlist, the winner under each Monte Carlo, and the decision."""
    b, w, st = result["stage_b"], result["stage_b"]["winner"], result["stability"]
    names = stageb.judge.stage_names(world["plan"])
    lines = [
        f"Etapa B · pool '{world['pool_name']}' plan {world['plan']['plan_key']}: "
        f"{len(b['table'])} finalistas diversas de {result['ranking_n']} carteras distintas "
        f"({len(world['search'])} evaluadas en la etapa A) × {b['n_settings']} riesgos"
    ]
    lines += [
        f"AJUSTADO: umbrales relajados {world['base']['relaxed']} — no es un resultado"
    ] * bool(world["base"]["relaxed"]) + pool_mod.prohibited_lines(
        world["pool_name"], world["base"]
    )
    for row in b["table"].sort_values("p", ascending=False).head(10).itertuples():
        risk = "/".join(f"{getattr(row, 'r_' + n):.1%}" for n in names)
        lines.append(
            f"  K={row.k} A={row.score:.3f} B={row.p:.3f} r={risk} decide {row.flavour}"
            f"@{row.length} · D {row.p_D:.3f} T1 {row.p_T1:.3f} T2 {row.p_T2:.3f} "
            f"[{', '.join(m[:8] for m in row.members.split('+'))}]"
        )
    lines.append(
        f"Ganadora: P(aprobar) {w['p_fresh']:.3f} en caminos nuevos (la búsqueda la eligió "
        f"con {w['p']:.3f}, el mejor de muchos sorteos) con el Monte Carlo más pesimista "
        f"({w['flavour']}{', bloque ' + str(w['length']) if w['length'] else ''}); tarda {w['t_median']:.0f} días de "
        f"mediana (p90 {w['t_p90']:.0f}) entre las que aprueban; {w['p_open']:.1%} siguen "
        f"abiertas al acabar el horizonte; rompe pérdida diaria {w['fail_daily_loss']:.1%}, "
        f"pérdida máxima {w['fail_max_loss']:.1%}, plazo {w['fail_time_limit']:.1%}"
    )
    lines.append(
        f"Estabilidad: {st['runs']} repeticiones, dispersión {st['spread']:.3f} — "
        + (
            "INSUFICIENTE: sube stageb.n_paths antes de decidir"
            if st["unstable"]
            else "los caminos sorteados bastan"
        )
    )
    if world["plan"]["flags"]:
        lines.append(
            f"Reglas sin confirmar: {[f['rule_key'] for f in world['plan']['flags']]}"
        )
    if world.get("clock_unconfirmed"):
        lines.append(
            f"Reloj del servidor de {world['firm']} sin confirmar: el día se corta donde "
            "dice config.yaml (equity.firm_clocks)"
        )
    if result["verdict"] is None:
        lines.append(
            f"Decisión: NINGUNA todavía — {result['reason']}. La etapa B elige mirando "
            f"solo build ({len(b['table'])} carteras × {b['n_settings']} riesgos de "
            f"{len(world['identities'])} estrategias admisibles): su P(aprobar) está "
            "inflada por la búsqueda y no autoriza a comprar el plan."
        )
    else:
        lines.append(decide.sentence(result["verdict"]))
    text = "\n".join(lines)
    print(text)
    return text


def main() -> None:
    """Stage B and the verdict for one stage-A run; files next to it, ledger rows, Spanish summary."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="semilla de los sorteos; queda en lo que se escribe",
    )
    args = parser.parse_args()
    cfg = config.load(args.overrides)
    refuse_unset(cfg)
    start = time.perf_counter()
    root_seed = args.seed
    world = load(args.run, args.overrides)
    result = build(world, cfg, np.random.default_rng(root_seed))
    declared = pool_mod.declared(world["pool_name"], world["base"])
    members = _union([result["stage_b"]["table"]])
    trials.record_b(
        result["stage_b"],
        declared,
        world["plan"]["plan_key"],
        {m: world["meta"][m] for m in members},
    )
    out = target(args.run)
    write(
        out,
        result,
        {
            "root_seed": root_seed,
            "wall_s": time.perf_counter() - start,
            "relaxed": cfg["relaxed"],
            "peak_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        },
    )
    text = summarise(world, result)
    if out != args.run:
        print(
            f"Esta run ya tenía etapa B: la nueva queda en una run aparte, {out.name}; la anterior no se toca."
        )
    if result["verdict"] is not None:
        chosen = result["verdict"]["chosen"]["members"]
        handoff.write(
            out,
            world["pool_name"],
            declared,
            chosen,
            dict.fromkeys(chosen, 1 / len(chosen)),
            world["universe"]["daily"],
            world["calendar"],
            result["verdict"],
            text.splitlines()[-1],
            world["base"],
        )


if __name__ == "__main__":
    main()
