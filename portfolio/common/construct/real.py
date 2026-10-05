"""THE COMMAND: choose a portfolio by ranks on build (M3) -- universe, sizing, pair screen, search."""

import argparse
import json
from datetime import datetime, timezone as tz
from pathlib import Path

import numpy as np
import pandas as pd

from core.datapaths import portfolio_dir
from core.manifest import fresh_dir

from .equity import matrix, universe
from .funded import _member_meta, size_members
from .inputs import config, pool as pool_mod
from .pairs import table as pairs_table
from portfolio.common.construct.search import admissible, admission, choose, objective, trials_real
from portfolio.common.construct.verdict import decide, metrics

RUNS = portfolio_dir() / "runs"
REQUIRED = {"losing_year": metrics.LOSING_YEAR, "shift_minimum": objective.SHIFT_MINIMUM}


def floor_risk(factors: dict, cfg: dict) -> dict[str, float]:
    """Each member's smallest risk per trade, as a fraction of the account, at the minimum lot.

    Below it the member's smallest trade rounds to no lot at all (the same half-lot rounding
    as the funded search, `search/stagea.py`).
    """
    lot, account = float(cfg["funded"]["min_lot"]), float(cfg["real"]["account"])
    return {i: (lot / 2) / (f["min_size"] * f["factor"] * account) for i, f in factors.items()}


def on_build(daily: pd.DataFrame, calendar: dict, scale: np.ndarray, cfg: dict) -> dict:
    """All the search may read: the build rows of the universe, their pair screen, and no later day.

    Args:
        daily: days x members daily P&L over every segment (`universe.load()["daily"]`).
        calendar: The portfolio calendar, naive Timestamps.
        scale: [N] each member's fixed-risk factor.
        cfg: The construct config.

    Returns:
        `unit` ([N, D] build daily P&L per unit of risk), `dates`, `graph`
        (`admissible.admissible`'s dict).
    """
    build_daily = matrix.segment(daily, calendar, "build")
    pairs = pairs_table.table(build_daily, matrix.monthly(build_daily), cfg)
    # ponytail: a day before a member's history counts as 0 for the combination; cut every
    # combination to its members' common history if pools ever mix very different spans
    unit = np.nan_to_num(build_daily.to_numpy().T) * scale[:, None]
    return {"unit": unit, "dates": build_daily.index,
            "graph": admissible.admissible(pairs, list(daily.columns), cfg)}


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
        `root_seed`, and what the verdict reads later -- `daily` (every segment), `calendar`,
        `scale`; no `unit` and `found` None when nothing is usable.
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
              "account": float(cfg["real"]["account"]), "relaxed": cfg["relaxed"],
              "prohibited": pool_mod.prohibited_lines(pool_name, cfg),
              "shift": f"{cfg['real']['shift_months']} meses, mínimo «{cfg['real']['shift_minimum']}»"}
    if not usable:
        return result

    calendar = {k: (pd.Timestamp(v[0]), pd.Timestamp(v[1]))
                for k, v in data["manifest"]["calendar"].items()}
    scale = np.array([factors[i]["factor"] for i in usable])
    result.update(on_build(data["daily"][usable], calendar, scale, cfg), calendar=calendar,
                  daily=data["daily"][usable], scale=scale,
                  members_meta={i: _member_meta(i) for i in usable})
    if search:
        result["found"] = choose.choose(result["unit"], result["dates"], result["graph"]["graph"],
                                        cfg, np.random.default_rng(root_seed))
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
    out = fresh_dir(RUNS / f"{datetime.now(tz.utc).strftime('%Y-%m-%dT%H%M')}_{result['pool_name']}_real")
    table.to_parquet(out / "search.parquet")
    best = table.iloc[result["found"]["best"]]
    manifest = {"pool": result["pool_name"], "mode": result["found"]["mode"],
                "root_seed": result["root_seed"], "n_scored": len(table),
                "n_reference": result["found"]["n_reference"],
                "relaxed": result["relaxed"], "shift": result["shift"],
                "identities": result["identities"], "best_members": best["members"].split("+"),
                "best": best.drop("members").to_dict(), "excluded": result["excluded"],
                "verdict": None}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=float), encoding="utf-8")
    return out


def summarise(result: dict, table: pd.DataFrame | None, out: Path | None) -> str:
    """The Spanish report: who was left out, the portfolio chosen with its cost, no verdict yet."""
    lines = [f"Pool '{result['pool_name']}': {len(result['kept'])} miembros en el universo, "
             f"{len(result['identities'])} utilizables"]
    if result["relaxed"]:
        lines.append(f"AJUSTADO: umbrales relajados {result['relaxed']} — no es un resultado")
    lines += result["prohibited"] + [f"  excluida {i[:12]}…: {why}" for i, why in result["excluded"]]
    if table is None:
        lines.append("Ningún miembro utilizable: no hay búsqueda.")
        return "\n".join(lines)
    found, best = result["found"], table.iloc[result["found"]["best"]]
    k, risk = int(best["k"]), float(best["floor_risk"])
    names = ", ".join(i[:8] for i in best["members"].split("+"))
    lines += [
        f"Búsqueda {found['mode']}: {len(table)} combinaciones admisibles evaluadas en build; "
        f"rangos tomados entre {found['n_reference']}; inicio desplazado 0…{result['shift']}",
        f"CARTERA ELEGIDA: K={k} [{names}] · puntuación {best['score']:.3f} (0-1, media de los "
        f"rangos de las 4 métricas) · deja fuera {len(result['identities']) - k} estrategias",
        f"  al lote mínimo en {decide.grouped(result['account'])}: {risk:.3%} por operación y miembro, "
        f"{k * risk:.3%} del balance arriesgado a la vez si coinciden los {k}",
        f"  RAR {100 * k * risk * best['rar']:.3f} %/año · R³ {best['r_cubed']:.2f} · "
        f"gain-to-pain {best['gain_to_pain']:.2f} · P(año perdedor) {best['p_losing_year']:.0%} "
        f"· Sharpe diario {best['sharpe']:.3f}",
        "Sin veredicto: es la elección en build; el juicio en oos1 y oos2 es el hito M5.",
    ]
    if out is not None:
        lines.append(f"Carpeta: {out}")
    return "\n".join(lines)


def admit(result: dict, base_run: Path, how: str) -> pd.DataFrame:
    """Every usable strategy outside a run's chosen portfolio, admitted in sequence (Q16 c)."""
    ids = result["identities"]
    chosen = set(json.loads((base_run / "manifest.json").read_text())["best_members"])
    base = np.array([n for n, i in enumerate(ids) if i in chosen])
    rest = np.array([n for n, i in enumerate(ids) if i not in chosen])
    judged = admission.sequence(result["unit"], result["graph"]["graph"], base, rest, how)
    return judged.assign(candidate=[ids[c] for c in judged["candidate"]],
                         blocked_by=[len(b) for b in judged["blocked_by"]])


def admitted(result: dict, judged: pd.DataFrame, how: str) -> str:
    """The admission pass in Spanish: every judgement, who entered and in what order."""
    lines = [f"AJUSTADO: umbrales relajados {result['relaxed']} — no es un resultado"] * bool(result["relaxed"])
    lines.append(judged.to_string(index=False))
    entered = judged.loc[judged["enters"], "candidate"].tolist()
    lines.append(f"Entran {len(entered)} de {judged['candidate'].nunique()}, en este orden: "
                 f"{', '.join(c[:8] for c in entered) or 'ninguna'}. Una por ronda: la de mayor "
                 f"incremento «{how}» del Sharpe en build entre las que no veta ninguna pareja; "
                 "la base crece y las demás se vuelven a juzgar contra ella.")
    return "\n".join(lines)


def main() -> None:
    """Search a pool's portfolio by ranks, or judge the outsiders against an earlier run's."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", required=True)
    parser.add_argument("--firm", help="empresa cuyas prohibiciones se quitan del pool")
    parser.add_argument("--base", type=Path, help="carpeta de una run: juzga la admisión a su cartera")
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()

    cfg = pool_mod.scoped(config.load(args.overrides), args.firm)
    need = {**REQUIRED, **({"increment": admission.INCREMENTS} if args.base else {})}
    for key, allowed in need.items():
        if cfg["real"][key] not in allowed:
            raise SystemExit(f"real.{key} no tiene valor y no lleva defecto: --set real.{key}="
                             f"{'|'.join(allowed)}")
    result = build(args.pool, cfg, search=not args.base)
    if "unit" not in result:
        print(summarise(result, None, None))
        return
    note = f"relaxed={cfg['relaxed'] or 'no'}"
    if args.base:
        judged = admit(result, args.base, cfg["real"]["increment"])
        judged.to_csv(args.base / "admission.csv", index=False)
        trials_real.record_admission(judged, pool_mod.declared(args.pool, cfg),
                                     result["members_meta"], cfg["real"]["increment"], note)
        print(admitted(result, judged, cfg["real"]["increment"]))
        return
    table = frame(result)
    out = write_run(result, table)
    trials_real.record(result["found"], pool_mod.declared(args.pool, cfg),
                       result["members_meta"], f"{result['found']['mode']}; {note}")
    print(summarise(result, table, out))


if __name__ == "__main__":
    main()
