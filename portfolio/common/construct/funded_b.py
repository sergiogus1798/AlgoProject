"""THE COMMAND: stage B and the funded verdict on an existing stage-A run."""

import argparse
import json
import resource
import time
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from core import fanout
from core.archive import read as archive_read
from core.barstore import source as bars_of
from portfolio.funded.rules import catalog

from . import funded
from .equity import universe
from .inputs import config, pool as pool_mod, source
from .pairs import table as pairs_table
from .search import (admissible, shortlist, stagea, stagea_data, stageb, stageb_data, stageb_null,
                     stageb_run, trials)
from .verdict import decide, hold, null as null_mod

REQUIRED = {"shared_of": ("smaller", "larger"), "t1_gap": ("close_to_open_blocks",)}
JUDGE = ("oos1", "oos2")
OWN = ("stageb.", "verdict.")       # knobs that never change the universe a run is read from


def refuse_unset(cfg: dict) -> None:
    """Stop when a knob with more than one reading was left empty (root CLAUDE.md, rule 11)."""
    for key, allowed in REQUIRED.items():
        if cfg["stageb"][key] not in allowed:
            raise SystemExit(f"stageb.{key} no está fijado: elige entre {list(allowed)} con "
                             f"--set stageb.{key}=<valor>; no hay valor por defecto.")


def load(run: Path, overrides: list[str]) -> dict:
    """Everything a stage-A run's folder points at, read from the archive and the universe.

    Returns:
        The world `build()` reads: `pool_name`, `plan`, `search` (`search.parquet`),
        `universe` (`equity.store.load()`), `firm`, `calendar`, `identities` and `graph` (the
        admissible graph over the members with a step-24 stop), `sources`, `bars` (per feed),
        `factors`, `min_size`, `meta` (identity -> symbol, timeframe, family),
        `clock_unconfirmed` (the firm's server clock is flagged in `config.yaml`).
    """
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    plan = catalog.plan(manifest["plan"])
    base = config.load([o for o in overrides if not o.startswith(OWN)])
    data = universe.load(universe.build(manifest["pool"], base))
    sized, _ = funded.size_members(data["manifest"]["members"]["kept"])
    identities = list(sized)
    calendar = {k: (pd.Timestamp(v[0]), pd.Timestamp(v[1]))
                for k, v in data["manifest"]["calendar"].items()}
    lo, hi = calendar["build"]
    build = data["daily"][identities].loc[lo:hi]      # months summed from build's own days
    pairs = pairs_table.table(build, build.groupby(build.index.to_period("M")).sum(min_count=1), base)
    sources = {i: source.load(i, archive_read.versions(i)[-1]) for i in identities}
    feeds = sorted({s["feed"] for s in sources.values()})
    return {"pool_name": manifest["pool"], "plan": plan,
            "search": pd.read_parquet(run / "search.parquet"), "universe": data,
            "firm": plan["firm"], "calendar": calendar, "identities": identities,
            "clock_unconfirmed": plan["firm"] in base["equity"]["unconfirmed_clocks"],
            "graph": admissible.admissible(pairs, identities, base)["graph"], "sources": sources,
            "bars": {f: bars_of(f, ["High", "Low", "Close"]) for f in feeds},
            "factors": {i: s["factor"] for i, s in sized.items()},
            "min_size": {i: s["min_size"] for i, s in sized.items()},
            "meta": {i: funded._member_meta(i) for i in identities}}


def _prepare(world: dict, members: list[str], span: tuple, cfg: dict) -> dict:
    """`stageb_data.prepare` for some members of the world on one stretch of server days."""
    return stageb_data.prepare({m: world["sources"][m] for m in members}, world["bars"],
                               world["universe"]["days"][world["firm"]],
                               cfg["equity"]["firm_clocks"][world["firm"]], span, world["factors"],
                               world["min_size"], cfg)


def _union(frames: list[pd.DataFrame]) -> list[str]:
    """Every identity some combination of the frames holds."""
    return sorted({m for f in frames for members in f["members"] for m in members.split("+")})


def _null_shortlists(world: dict, cfg: dict, rng: np.random.Generator) -> tuple[list, int]:
    """The null searches' shortlists: random admissible combinations scored by stage A."""
    prepared = stagea_data.prepare(world["universe"], world["firm"], world["identities"],
                                   world["calendar"], world["factors"], world["min_size"])
    sizes = (world["search"]["members"].str.count(r"\+") + 1).to_numpy()
    n = cfg["verdict"]["null_candidates"] or len(world["search"])

    def score(combos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Stage A's objective: each row's best P(pass) over the risk grid, and that level."""
        return stagea.best(stagea.evaluate(prepared, combos, world["plan"], cfg),
                           cfg["funded"]["risk_grid"])

    return [stageb_null.shortlisted(score, world["graph"], world["identities"], sizes, n, cfg, rng)
            for _ in range(cfg["verdict"]["null_draws"])], n


def build(world: dict, cfg: dict, rng: np.random.Generator) -> dict:
    """Stage B on the run's shortlist, then the verdict when the judging segments exist.

    Returns:
        `stage_b` (`stageb_run.run()`; its `winner` gains `p_fresh`, the P(pass) to report: the
        stability re-draws' mean, where `p` is the selector's), `stability`, `ranking_n` (distinct combinations of the
        search), `verdict` (`verdict.decide.verdict()`, or None with `reason`), `nulls` (each
        null search's winner and measures), `segments`.
    """
    refuse_unset(cfg)
    numba.set_num_threads(min(fanout.CORES, numba.config.NUMBA_NUM_THREADS))
    plan, calendar = world["plan"], world["calendar"]
    ranking = shortlist.ranked(world["search"])
    sb = cfg["stageb"]
    short = shortlist.diverse(ranking, sb["shortlist_size"], sb["max_shared"], sb["shared_of"])
    table = world["universe"]["days"][world["firm"]]
    segments = [s for s in JUDGE if s in calendar and
                table["day"].between(*calendar[s]).any()]
    out = {"ranking_n": len(ranking), "segments": segments, "verdict": None, "nulls": []}
    judging = segments == list(JUDGE)
    nulls, n_candidates = _null_shortlists(world, cfg, rng) if judging else ([], 0)

    data = _prepare(world, _union([short, *nulls]), calendar["build"], cfg)
    out["stage_b"] = b = stageb_run.run(short, data, plan, cfg, rng)
    winner = b["winner"]
    risk = stageb_run.risk_of(winner, plan)
    out["stability"] = stageb.stability(data, stageb_run.rows_of(data, winner["members"]), plan,
                                        cfg, risk, rng.spawn(1)[0])
    # `p` chose the winner — the best of shortlist × risks noisy figures, so it reads high; what
    # is reported is the same figure on fresh paths from an independent seed
    winner["p_fresh"] = out["stability"]["mean"]
    if not judging:
        out["reason"] = (f"sin {' ni '.join(s for s in JUDGE if s not in segments)} en el "
                         "universo: el veredicto se juzga en oos1+oos2 juntos y no se emite")
        return out

    null_winners = [stageb_run.run(n, data, plan, cfg, rng)["winner"] for n in nulls]
    chosen = winner["members"].split("+")
    trials.admit({m: world["meta"][m] for m in chosen}, segments)
    span = (calendar[JUDGE[0]][0], calendar[JUDGE[1]][1])
    later = _prepare(world, _union([pd.DataFrame([winner, *null_winners])]), span, cfg)
    real = stageb_run.judged(later, winner["members"], plan, cfg, risk, rng)
    for w in null_winners:
        got = stageb_run.judged(later, w["members"], plan, cfg, stageb_run.risk_of(w, plan), rng)
        out["nulls"].append({"members": w["members"], "selector_p": w["p"],
                             "start_p": got["start_p"], "mc_p": got["mc_p"]})
    out["judged"] = real
    daily = world["universe"]["daily"][chosen].loc[span[0]:span[1]]
    pairs = pairs_table.table(daily, daily.groupby(daily.index.to_period("M")).sum(min_count=1), cfg)
    cost = {"n_pool": len(world["identities"]), "n_stage_a": len(world["search"]),
            "n_shortlist": len(short), "n_settings": b["n_settings"],
            "null_draws": len(nulls), "null_candidates": n_candidates, "segments": segments}
    out["verdict"] = decide.verdict(
        {"members": chosen, "build_p": winner["p_fresh"], "selector_p": winner["p"],
         "risk": dict(zip(stageb.judge.stage_names(plan), risk[0].tolist()))},
        null_mod.read({"start_p": real["start_p"], "mc_p": real["mc_p"]}, out["nulls"]),
        hold.held(pairs, chosen, cfg), cost, cfg)
    return out


def write(run: Path, result: dict, extra: dict) -> None:
    """`shortlist.parquet`, `stageb.parquet` and `verdict.json`, next to the stage-A run's files."""
    b = result["stage_b"]
    b["table"].to_parquet(run / "shortlist.parquet")
    b["rows"].to_parquet(run / "stageb.parquet")
    judged = result.get("judged")
    blob = {"winner": b["winner"], "stability": result["stability"],
            "segments": result["segments"], "verdict": result["verdict"],
            "reason": result.get("reason"), "nulls": result["nulls"],
            "judged": None if judged is None else {k: v for k, v in judged.items() if k != "rows"},
            **extra}
    (run / "verdict.json").write_text(
        json.dumps(blob, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
        encoding="utf-8")
    if judged is not None:
        judged["rows"].to_parquet(run / "verdict_rows.parquet")


def summarise(world: dict, result: dict) -> str:
    """The Spanish report: the shortlist, the winner under each Monte Carlo, and the decision."""
    b, w, st = result["stage_b"], result["stage_b"]["winner"], result["stability"]
    names = stageb.judge.stage_names(world["plan"])
    lines = [f"Etapa B · pool '{world['pool_name']}' plan {world['plan']['plan_key']}: "
             f"{len(b['table'])} finalistas diversas de {result['ranking_n']} carteras distintas "
             f"({len(world['search'])} evaluadas en la etapa A) × {b['n_settings']} riesgos"]
    for row in b["table"].sort_values("p", ascending=False).head(10).itertuples():
        risk = "/".join(f"{getattr(row, 'r_' + n):.1%}" for n in names)
        lines.append(f"  K={row.k} A={row.score:.3f} B={row.p:.3f} r={risk} decide {row.flavour}"
                     f"@{row.length} · D {row.p_D:.3f} T1 {row.p_T1:.3f} T2 {row.p_T2:.3f} "
                     f"[{', '.join(m[:8] for m in row.members.split('+'))}]")
    lines.append(f"Ganadora: P(aprobar) {w['p_fresh']:.3f} en caminos nuevos (la búsqueda la eligió "
                 f"con {w['p']:.3f}, el mejor de muchos sorteos) con el Monte Carlo más pesimista "
                 f"({w['flavour']}{', bloque ' + str(w['length']) if w['length'] else ''}); tarda {w['t_median']:.0f} días de "
                 f"mediana (p90 {w['t_p90']:.0f}) entre las que aprueban; {w['p_open']:.1%} siguen "
                 f"abiertas al acabar el horizonte; rompe pérdida diaria {w['fail_daily_loss']:.1%}, "
                 f"pérdida máxima {w['fail_max_loss']:.1%}, plazo {w['fail_time_limit']:.1%}")
    lines.append(f"Estabilidad: {st['runs']} repeticiones, dispersión {st['spread']:.3f} — "
                 + ("INSUFICIENTE: sube stageb.n_paths antes de decidir" if st["unstable"]
                    else "los caminos sorteados bastan"))
    if world["plan"]["flags"]:
        lines.append(f"Reglas sin confirmar: {[f['rule_key'] for f in world['plan']['flags']]}")
    if world.get("clock_unconfirmed"):
        lines.append(f"Reloj del servidor de {world['firm']} sin confirmar: el día se corta donde "
                     "dice config.yaml (equity.firm_clocks)")
    if result["verdict"] is None:
        lines.append(f"Decisión: NINGUNA todavía — {result['reason']}. La etapa B elige mirando "
                     f"solo build ({len(b['table'])} carteras × {b['n_settings']} riesgos de "
                     f"{len(world['identities'])} estrategias admisibles): su P(aprobar) está "
                     "inflada por la búsqueda y no autoriza a comprar el plan.")
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
    args = parser.parse_args()
    cfg = config.load(args.overrides)
    refuse_unset(cfg)
    start = time.perf_counter()
    rng = np.random.default_rng()
    root_seed = int(rng.integers(0, 2**63 - 1))
    world = load(args.run, args.overrides)
    result = build(world, cfg, np.random.default_rng(root_seed))
    declared = pool_mod.read(world["pool_name"], cfg.get("pool", {}).get("firm"))
    members = _union([result["stage_b"]["table"]])
    trials.record_b(result["stage_b"], declared, world["plan"]["plan_key"],
                    {m: world["meta"][m] for m in members})
    if result["verdict"] is not None:
        trials.record_verdict(result["verdict"], declared, world["plan"]["plan_key"],
                              {m: world["meta"][m] for m in result["verdict"]["chosen"]["members"]},
                              result["segments"])
    write(args.run, result, {"root_seed": root_seed, "wall_s": time.perf_counter() - start,
                             "peak_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024})
    summarise(world, result)


if __name__ == "__main__":
    main()
