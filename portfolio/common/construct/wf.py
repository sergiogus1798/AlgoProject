"""THE COMMAND: the weight walk-forward (M8) -- does any method beat equal weight on oos1, fixed or only re-estimated."""

import argparse
import hashlib
import json
from datetime import datetime
from datetime import timezone as tz
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from core import manifest, paths

from . import real, walkforward, weights
from .equity import matrix
from .inputs import config
from .inputs import pool as pool_mod
from .inputs.pool import Pool
from .search import trials
from .walkforward import Walkforward

ROOT = paths.portfolio_dir() / "weights_wf"
CRITERION = "portfolio/weights_wf"
ARM = {"fixed": "fijo", "reestimated": "re-estimado"}


def members_of(result: dict, run: Path | None, given: str | None) -> list[str]:
    """The portfolio to weigh: a run's chosen members, or identities given by prefix."""
    if given:
        found = [
            [i for i in result["identities"] if i.startswith(p)]
            for p in given.split(",")
        ]
        if any(len(f) != 1 for f in found):
            raise SystemExit(
                f"--members: cada prefijo debe nombrar UNA estrategia utilizable del pool: {given}"
            )
        return sorted(f[0] for f in found)
    assert run is not None
    members = json.loads((run / "manifest.json").read_text(encoding="utf-8"))[
        "best_members"
    ]
    if missing := [m[:12] for m in members if m not in result["identities"]]:
        raise SystemExit(
            f"la cartera de {run.name} tiene miembros no utilizables con esta configuración: {missing}"
        )
    return sorted(members)


def run(
    result: dict, members: list[str], cfg: dict, rng: np.random.Generator
) -> Walkforward:
    """Ask the door, cut build (estimation) and oos1 (test), walk every method and compare.

    Args:
        result: `real.build(search=False)`'s result, or a test's stand-in with `daily`,
            `calendar`, `scale`, `identities`, `members_meta`.
        members: The portfolio, at least two identities.
        cfg: The construct config (`wf`, `real.losing_year`).
        rng: Draws the bootstrap.

    Returns:
        `walkforward.arms()`'s dict plus `table` (`compare`), `states` (`decide`), `cuts`,
        `members`, `meta`, `build`, `test` (each a (first day, last day) pair).
    """
    meta = {i: result["members_meta"][i] for i in members}
    trials.admit(meta, ["build", "oos1"])
    scale = pd.Series(result["scale"], index=result["identities"])[members]
    parts = [
        matrix.segment(result["daily"][members], result["calendar"], s)
        for s in ("build", "oos1")
    ]
    unit = pd.concat(parts).fillna(0.0) * scale
    if parts[1].empty:
        raise SystemExit(
            "la cartera no tiene días en oos1: no hay dónde probar los pesos"
        )
    cuts = walkforward.folds(
        pd.DatetimeIndex(unit.index),
        cast(pd.Timestamp, parts[1].index[0]),
        int(cfg["wf"]["lookback_years"]),
        int(cfg["wf"]["step_years"]),
    )
    got = walkforward.arms(unit, cuts, weights.REGISTRY, cfg)
    table = walkforward.compare(got, cfg, rng)
    return {
        "paths": got["paths"],
        "dates": got["dates"],
        "weights": got["weights"],
        "failed": got["failed"],
        "table": table,
        "states": walkforward.decide(table),
        "cuts": cuts,
        "members": members,
        "meta": meta,
        "build": (
            cast(pd.Timestamp, parts[0].index[0]),
            cast(pd.Timestamp, parts[0].index[-1]),
        ),
        "test": (
            cast(pd.Timestamp, parts[1].index[0]),
            cast(pd.Timestamp, parts[1].index[-1]),
        ),
    }


def record(got: Walkforward, pool: Pool, cfg: dict) -> list[dict]:
    """One ledger row per segment read (PLAN §6): build estimates, oos1 compares every arm.

    The arms' Sharpes carry their own unit: they count in N and stay out of the study's pooled
    sigma, which seven weightings of one portfolio would only narrow.
    """
    table, note = (
        got["table"],
        f"walk-forward de pesos, K={len(got['members'])}; relaxed={cfg['relaxed'] or 'no'}",
    )
    methods = table["method"].nunique()
    base = {"launched_by": "wf", "criterion": CRITERION, "note": note}
    return trials.record_rows(
        pool,
        got["meta"],
        {**base, "segment": "build", "n_in": methods, "n_out": methods},
    ) + trials.record_rows(
        pool,
        got["meta"],
        {
            **base,
            "segment": "oos1",
            "n_in": len(table),
            "n_out": int(table["beats"].sum()),
            "score_unit": "sharpe_weight_arm",
        },
        table["sharpe"].to_numpy(),
    )


def sentence(got: Walkforward, cfg: dict) -> str:
    """The decision in Spanish, the cost next to it; it changes no knob."""
    states, table = got["states"], got["table"]
    cost = (
        f"{len(table) - 1} brazos comparados con pesos iguales sobre {len(got['dates'])} días de oos1, intervalo al "
        f"{float(cfg['wf']['confidence']):.0%} sin corregir por el número de comparaciones"
    )
    fixed = [m for m, s in states.items() if s == "fixed"]
    only = [m for m, s in states.items() if s == "only_reestimated"]
    if only:
        text = (
            f"{', '.join(only)} solo gana a pesos iguales re-estimando: se cumple la condición que revierte "
            "DECISIONS #5 (no rebalancear nunca). Lo decide el dueño"
        )
    elif fixed:
        text = (
            f"{', '.join(fixed)} gana a pesos iguales con los pesos fijados una vez: candidato a que el dueño lo "
            "seleccione; DECISIONS #5 (no rebalancear) se mantiene"
        )
    else:
        text = "se mantienen los pesos iguales: ningún método les gana fuera de muestra, ni fijo ni re-estimado"
    return f"DECISIÓN: {text} ({cost})."


def summarise(got: Walkforward, pool_name: str, cfg: dict) -> str:
    """The Spanish text the owner reads: windows, one line per arm, the weights held, the decision."""
    wf, t = cfg["wf"], got["table"]
    look = (
        f"{wf['lookback_years']} años antes de cada tramo"
        if wf["lookback_years"]
        else "todo lo anterior a cada tramo"
    )
    lines = [
        f"Walk-forward de pesos — pool {pool_name}, cartera K={len(got['members'])} "
        f"[{', '.join(m[:8] for m in got['members'])}]",
        f"Estimación: build {got['build'][0].date()}…{got['build'][1].date()} ({look}). Prueba: oos1 "
        f"{got['test'][0].date()}…{got['test'][1].date()}, {len(got['dates'])} días en {len(got['cuts'])} tramo(s) "
        f"de {wf['step_years']} año(s). oos2 no se abre.",
        f"{'método':<13}{'brazo':<13}{'Sharpe/día':>10}{'RAR':>9}{'R³':>8}{'G/P':>7}{'P(año−)':>9}   Sharpe − pesos iguales [intervalo]   gana",
    ]
    for r in t.to_dict("records"):
        versus = (
            ""
            if r["method"] == "equal"
            else f"{r['diff']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}]"
        )
        extra = (
            f"   vs fijo {r['diff_fixed']:+.4f} [{r['lo_fixed']:+.4f}, {r['hi_fixed']:+.4f}]"
            if r["arm"] == "reestimated"
            else ""
        )
        lines.append(
            f"{r['method']:<13}{ARM[r['arm']]:<13}{r['sharpe']:>10.4f}{r['rar']:>9.3f}{r['r_cubed']:>8.2f}"
            f"{r['gain_to_pain']:>7.2f}{r['p_losing_year']:>9.2f}   {versus:<34} "
            f"{'' if r['method'] == 'equal' else 'sí' if r['beats'] else 'no'}{extra}"
        )
    first = got["weights"][got["weights"]["window"] == 0]
    lines += [
        f"Pesos fijados en build — {m}: "
        + ", ".join(f"{i[:8]} {w:.3f}" for i, w in zip(g["identity"], g["weight"]))
        for m, g in first.groupby("method", sort=False)
        if m != "equal"
    ]
    lines += [f"No se pudo estimar {m}: {why}" for m, why in got["failed"].items()]
    if len(got["cuts"]) == 1:
        lines.append(
            "Un solo tramo de prueba: re-estimar no cambia nada, los dos brazos son el mismo."
        )
    lines += [
        "Cómo leerlo: «fijo» = pesos estimados una vez en build y mantenidos; «re-estimado» = estimados de nuevo al "
        "empezar cada tramo. La diferencia es el Sharpe diario del brazo menos el de pesos iguales en los mismos días; "
        f"su intervalo sale de {wf['bootstrap_draws']} remuestreos por bloques (bloque medio {int(t['block'].iloc[0])} "
        "días). «Gana» = el intervalo entero queda por encima de 0.",
        sentence(got, cfg),
        "Este estudio no cambia nada: weights.method sigue en «equal» hasta que el dueño diga otra cosa.",
    ]
    return "\n".join(lines)


def write(got: Walkforward, pool_name: str, cfg: dict, source: str) -> Path:
    """`table.parquet`, `weights.parquet` and `result.json` under `weights_wf/<stamp>_<pool>_K<k>_<members' hash>/`."""
    tag = hashlib.sha256("+".join(got["members"]).encode()).hexdigest()[:8]
    out = manifest.fresh_dir(
        ROOT
        / f"{datetime.now(tz.utc).strftime('%Y-%m-%dT%H%M')}_{pool_name}_K{len(got['members'])}_{tag}"
    )
    got["table"].to_parquet(out / "table.parquet", index=False)
    got["weights"].to_parquet(out / "weights.parquet", index=False)
    blob = {
        "pool": pool_name,
        "members": got["members"],
        "source": source,
        "states": got["states"],
        "state_words": walkforward.STATES,
        "sentence": sentence(got, cfg),
        "failed": got["failed"],
        "windows": got["cuts"],
        "build": got["build"],
        "test": got["test"],
        "test_days": len(got["dates"]),
        "seed": got.get("seed"),
        "wf": cfg["wf"],
        "relaxed": cfg["relaxed"],
        "selected_method": cfg["weights"]["method"],
    }
    (out / "result.json").write_text(
        json.dumps(blob, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return out


def main() -> None:
    """Walk a portfolio's weights forward, log the looks, write the folder and print the decision."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", required=True)
    parser.add_argument("--firm", help="empresa cuyas prohibiciones se quitan del pool")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument(
        "--run",
        type=Path,
        help="carpeta de una run de real.py o report.py: su cartera elegida",
    )
    which.add_argument("--members", help="identidades por prefijo, separadas por comas")
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="semilla de los sorteos; queda en lo que se escribe",
    )
    args = parser.parse_args()
    cfg = pool_mod.scoped(config.load(args.overrides), args.firm)
    if cfg["wf"]["confidence"] is None:
        raise SystemExit(
            "wf.confidence no tiene valor y no lleva defecto: --set wf.confidence=<0..1> "
            "(el intervalo que una diferencia de Sharpe debe superar para «ganar»)"
        )
    result = real.build(args.pool, cfg, args.seed, search=False)
    if "unit" not in result:
        raise SystemExit(real.summarise(result, None, None))
    members = members_of(result, args.run, args.members)
    if len(members) < 2:
        raise SystemExit("la cartera tiene un solo miembro: no hay pesos que comparar")
    got = run(result, members, cfg, np.random.default_rng(args.seed))
    got["seed"] = args.seed
    record(got, pool_mod.declared(args.pool, cfg), cfg)
    out = write(got, args.pool, cfg, args.run.name if args.run else "--members")
    if cfg["relaxed"]:
        print(f"AJUSTADO: umbrales relajados {cfg['relaxed']} — no es un resultado")
    print(summarise(got, args.pool, cfg))
    print(f"Carpeta: {out} (table.parquet, weights.parquet, result.json)")


if __name__ == "__main__":
    main()
