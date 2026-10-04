"""THE COMMAND: choose a portfolio by ranks on build (M3) -- universe, sizing, pair screen, search."""

import argparse
import json
from datetime import datetime, timezone as tz
from pathlib import Path

import numpy as np
import pandas as pd

from core.datapaths import portfolio_dir

from .equity import matrix, universe
from .funded import _member_meta, size_members
from .inputs import config, pool as pool_mod
from .pairs import table as pairs_table
from portfolio.common.construct.search import admissible, admission, choose, trials_real
from portfolio.common.construct.verdict import metrics

RUNS = portfolio_dir() / "runs"
REQUIRED = {"losing_year": metrics.LOSING_YEAR}


def floor_risk(factors: dict, cfg: dict) -> dict[str, float]:
    """Each member's smallest risk per trade, as a fraction of the account, at the minimum lot.

    Below it the member's smallest trade rounds to no lot at all (the same half-lot rounding
    as the funded search, `search/stagea.py`).
    """
    lot, account = float(cfg["funded"]["min_lot"]), float(cfg["real"]["account"])
    return {i: (lot / 2) / (f["min_size"] * f["factor"] * account) for i, f in factors.items()}


def build(pool_name: str, cfg: dict, search: bool = True) -> dict:
    """Universe, fixed-risk sizing, the minimum-lot floor, the pair screen and the search.

    Args:
        pool_name: A declared pool.
        cfg: `inputs.config.load()`'s result.
        search: False prepares everything and searches nothing (the admission pass).

    Returns:
        `kept`, `excluded` ((identity, reason) pairs: no step-24 stop, or a floor above the
        risk grid's top), `identities` (graph order), `floor` (identity -> floor risk),
        `account`, `unit` ([N, D] build daily P&L per unit of risk), `dates`, `graph`
        (`admissible.admissible`'s dict), `found` (`choose.choose`'s), `members_meta`,
        `root_seed`; no `unit` and `found` None when nothing is usable.
    """
    root_seed = int(np.random.default_rng().integers(0, 2**63 - 1))
    data = universe.load(universe.build(pool_name, cfg))
    kept = data["manifest"]["members"]["kept"]
    factors, excluded = size_members(kept)
    floor = floor_risk(factors, cfg)
    top = max(cfg["funded"]["risk_grid"])
    excluded += [(i, f"lote mínimo: exige {r:.2%} por operación, más que el {top:.2%} de la rejilla")
                 for i, r in floor.items() if r > top]
    out_of = {i for i, _ in excluded}
    usable = [i for i in kept if i not in out_of]
    result = {"pool_name": pool_name, "kept": kept, "excluded": excluded, "identities": usable,
              "floor": floor, "found": None, "root_seed": root_seed,
              "account": float(cfg["real"]["account"])}
    if not usable:
        return result

    calendar = {k: (pd.Timestamp(v[0]), pd.Timestamp(v[1]))
                for k, v in data["manifest"]["calendar"].items()}
    build_daily = matrix.segment(data["daily"][usable], calendar, "build")
    pairs = pairs_table.table(build_daily, matrix.monthly(build_daily), cfg)
    graph = admissible.admissible(pairs, usable, cfg)
    scale = np.array([factors[i]["factor"] for i in usable])
    # ponytail: a day before a member's history counts as 0 for the combination; cut every
    # combination to its members' common history if pools ever mix very different spans
    unit = np.nan_to_num(build_daily.to_numpy().T) * scale[:, None]
    result.update(unit=unit, dates=build_daily.index, graph=graph,
                  members_meta={i: _member_meta(i) for i in usable})
    if search:
        result["found"] = choose.choose(unit, build_daily.index, graph["graph"], cfg,
                                        np.random.default_rng(root_seed))
    return result


def frame(result: dict) -> pd.DataFrame:
    """One row per combination evaluated: members, K, score, the four metrics, Sharpe, floor."""
    found, ids = result["found"], result["identities"]
    floor = np.array([result["floor"][i] for i in ids])
    members = found["members"]
    return pd.DataFrame({
        "members": ["+".join(ids[i] for i in np.flatnonzero(m)) for m in members],
        "k": members.sum(axis=1), "score": found["score"], **found["table"],
        "floor_risk": np.where(members, floor, 0.0).max(axis=1)})


def write_run(result: dict, table: pd.DataFrame) -> Path:
    """Write `search.parquet` and `manifest.json` under `RUNS/<stamp>_<pool>_real/`."""
    out = RUNS / f"{datetime.now(tz.utc).strftime('%Y-%m-%dT%H%M')}_{result['pool_name']}_real"
    out.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out / "search.parquet")
    best = table.iloc[result["found"]["best"]]
    manifest = {"pool": result["pool_name"], "mode": result["found"]["mode"],
                "root_seed": result["root_seed"], "n_scored": len(table),
                "n_reference": result["found"]["n_reference"],
                "identities": result["identities"], "best_members": best["members"].split("+"),
                "best": best.drop("members").to_dict(), "excluded": result["excluded"],
                "verdict": None}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=float), encoding="utf-8")
    return out


def summarise(result: dict, table: pd.DataFrame | None, out: Path | None) -> str:
    """The Spanish report: who was left out, the portfolio chosen with its cost, no verdict yet."""
    lines = [f"Pool '{result['pool_name']}': {len(result['kept'])} miembros en el universo, "
             f"{len(result['identities'])} utilizables"]
    lines += [f"  excluida {i[:12]}…: {why}" for i, why in result["excluded"]]
    if table is None:
        lines.append("Ningún miembro utilizable: no hay búsqueda.")
        return "\n".join(lines)
    found, best = result["found"], table.iloc[result["found"]["best"]]
    k, risk = int(best["k"]), float(best["floor_risk"])
    names = ", ".join(i[:8] for i in best["members"].split("+"))
    lines += [
        f"Búsqueda {found['mode']}: {len(table)} combinaciones admisibles evaluadas en build; "
        f"rangos tomados entre {found['n_reference']}",
        f"CARTERA ELEGIDA: K={k} [{names}] · puntuación {best['score']:.3f} (0-1, media de los "
        f"rangos de las 4 métricas) · deja fuera {len(result['identities']) - k} estrategias",
        f"  al lote mínimo en {result['account']:,.0f}: {risk:.2%} por operación y miembro, "
        f"{k * risk:.2%} del balance arriesgado a la vez si coinciden los {k}",
        f"  RAR {100 * k * risk * best['rar']:.1f} %/año · R³ {best['r_cubed']:.2f} · "
        f"gain-to-pain {best['gain_to_pain']:.2f} · P(año perdedor) {best['p_losing_year']:.0%} "
        f"· Sharpe diario {best['sharpe']:.3f}",
        "Sin veredicto: es la elección en build; el juicio en oos1 y oos2 es el hito M5.",
    ]
    if out is not None:
        lines.append(f"Carpeta: {out}")
    return "\n".join(lines)


def admit(result: dict, base_run: Path, how: str) -> pd.DataFrame:
    """Every usable strategy outside a run's chosen portfolio, judged against it (Q16 c)."""
    ids = result["identities"]
    chosen = set(json.loads((base_run / "manifest.json").read_text())["best_members"])
    base = np.array([n for n, i in enumerate(ids) if i in chosen])
    rest = np.array([n for n, i in enumerate(ids) if i not in chosen])
    judged = admission.judge(result["unit"], result["graph"]["graph"], base, rest, how)
    return judged.assign(candidate=[ids[c] for c in judged["candidate"]],
                         blocked_by=[len(b) for b in judged["blocked_by"]])


def main() -> None:
    """Search a pool's portfolio by ranks, or judge the outsiders against an earlier run's."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", required=True)
    parser.add_argument("--base", type=Path, help="carpeta de una run: juzga la admisión a su cartera")
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()

    cfg = config.load(args.overrides)
    need = {**REQUIRED, **({"increment": admission.INCREMENTS} if args.base else {})}
    for key, allowed in need.items():
        if cfg["real"][key] not in allowed:
            raise SystemExit(f"real.{key} no tiene valor y no lleva defecto: --set real.{key}="
                             f"{'|'.join(allowed)}")
    result = build(args.pool, cfg, search=not args.base)
    if "unit" not in result:
        print(summarise(result, None, None))
        return
    if args.base:
        judged = admit(result, args.base, cfg["real"]["increment"])
        judged.to_csv(args.base / "admission.csv", index=False)
        trials_real.record_admission(judged, pool_mod.read(args.pool, cfg.get("pool", {}).get("firm")),
                                     result["members_meta"], cfg["real"]["increment"])
        print(judged.to_string(index=False))
        print(f"Entrarían {int(judged['enters'].sum())} de {len(judged)}: incremento "
              f"«{cfg['real']['increment']}» del Sharpe en build > 0 y ninguna pareja vetada.")
        return
    table = frame(result)
    out = write_run(result, table)
    note = f"{result['found']['mode']}; relaxed={cfg['relaxed'] or 'no'}"
    trials_real.record(result["found"], pool_mod.read(args.pool, cfg.get("pool", {}).get("firm")),
                       result["members_meta"], note)
    print(summarise(result, table, out))


if __name__ == "__main__":
    main()
