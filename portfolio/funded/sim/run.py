"""THE COMMAND: the bank table of every universe plan on one path set, against the monkey, with the curve EV(h)."""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from core.paths import portfolio_dir
from core.study import config as study_config
from core.study import result as study_result
from portfolio.funded.sim import bank, inputs, monkey, report, table, trials
from portfolio.funded.sim.plans import Terms


class Ran(table.Built):
    """`table.build()`'s tables plus the study-contract `result`, the plan `variants`, what was `skipped` and the rule `flags`."""

    result: dict[str, Any]
    variants: list[Terms]
    skipped: dict[str, list[str]]
    flags: dict[str, dict]


def generated(args: argparse.Namespace, seed: int) -> tuple[dict, dict]:
    """A path set drawn now from a server-day table with stage B's block bootstrap (agent C's module)."""
    from portfolio.common.construct.mc import (
        paths as mc_paths,
    )  # lazy: this package runs without it

    frame = pd.read_parquet(args.days)
    days = {name: frame[name].to_numpy() for name in bank.ARRAYS}
    arrays = mc_paths.daily_blocks(
        days, args.horizon, args.n_paths, args.mean_block, np.random.default_rng(seed)
    )
    return arrays, {
        "unit_risk": args.unit_risk,
        "days_per_year": args.days_per_year,
        "synthetic": False,
        "label": Path(args.days).stem,
    }


def run(
    paths: dict,
    meta: dict,
    cfg: dict,
    out: Path,
    seed: int,
    zero: dict | None = None,
    ledger: dict | None = None,
) -> Ran:
    """Simulate, write `table.parquet`, `addons.parquet`, `search.parquet`, `result.json`, `manifest.json`.

    Args:
        paths, meta: `inputs.paths()`'s pair.
        cfg: The config; `inputs.refuse` and `table.variants` must have found nothing missing.
        out: Folder to write into.
        seed: Root of the denied-payout and firm-closure draws.
        zero: The monkey's path set; `None` = `monkey.zero_edge` under `cfg["monkey"]["model"]`.
        ledger: `study`, `symbol`, `segment` — where the search is counted; `None` only for a
            synthetic path set, which is not a look at data.

    Returns:
        `table.build()`'s dict plus `result` (the study-contract dict) and `variants`.
    """
    started = time.time()
    owner = cfg["owner"]
    variants, _, skipped = table.variants(cfg)
    n_paths, horizon = paths["closed"].shape
    hazards = bank.hazards(
        n_paths,
        horizon,
        owner["p_payout_denied"],
        owner["p_firm_closes_year"],
        meta["days_per_year"],
        np.random.default_rng(seed),
    )
    zero = zero or monkey.zero_edge(paths, cfg["monkey"]["model"])
    built = table.build(
        paths, zero, meta, cfg, variants, hazards, study_result.progress
    )
    flags: dict[str, dict] = {}
    for plan in variants:
        for f in plan["flags"]:
            flags.setdefault(f["rule_key"], {**f, "plans": set()})["plans"].add(
                plan["plan_key"]
            )
    result = report.contract(built, cfg, meta, flags, started)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("rows", "addons", "search"):
        pd.DataFrame(built[name]).to_parquet(
            out / f"{'table' if name == 'rows' else name}.parquet"
        )
    (out / "result.json").write_text(
        json.dumps(result, ensure_ascii=False), encoding="utf-8"
    )
    row = None
    if not meta["synthetic"]:
        assert ledger is not None  # a real-data run always comes with its ledger cell
        row = trials.record(
            ledger["study"],
            ledger["symbol"],
            ledger["segment"],
            built["search"],
            len(built["rows"]),
            study_config.fingerprint(cfg),
        )
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "paths": meta,
                "n_paths": n_paths,
                "horizon": horizon,
                "seed": seed,
                "config": cfg,
                "eurusd": owner["eurusd"],
                "catalogue_read": datetime.now().isoformat("T", "seconds"),
                "skipped_addons": skipped,
                "configurations": len(built["search"]),
                "ledger": row,
                "wall_s": round(time.time() - started, 2),
            },
            ensure_ascii=False,
            default=str,
            indent=1,
        ),
        encoding="utf-8",
    )
    return {
        "rows": built["rows"],
        "addons": built["addons"],
        "search": built["search"],
        "result": result,
        "variants": variants,
        "skipped": skipped,
        "flags": flags,
    }


def main() -> None:
    """Parse, refuse what the owner has not given, run, print the table and the sentence."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--paths", type=Path, help="path set .npz (inputs.paths)")
    parser.add_argument(
        "--days", type=Path, help="server-day table .parquet, to draw the paths now"
    )
    parser.add_argument("--horizon", type=int, help="with --days: path days per draw")
    parser.add_argument("--n-paths", type=int, help="with --days: draws")
    parser.add_argument(
        "--mean-block", type=float, help="with --days: mean block length, days"
    )
    parser.add_argument(
        "--unit-risk",
        type=float,
        help="with --days: currency risked per trade in the table",
    )
    parser.add_argument(
        "--days-per-year", type=float, help="with --days: server days in a year"
    )
    parser.add_argument(
        "--monkey",
        type=Path,
        help="path set .npz of the monkey, instead of monkey.model",
    )
    parser.add_argument("--study", help="ledger study the search is counted in")
    parser.add_argument("--symbol", help="the members' symbols joined with +")
    parser.add_argument("--segment", help="the segment the path set was built from")
    parser.add_argument(
        "--seed", type=int, help="root of the random draws; fresh when absent"
    )
    parser.add_argument(
        "--out", type=Path, help="output folder (default AlgoData/portfolio/bank/…)"
    )
    parser.add_argument(
        "--set", action="append", default=[], metavar="section.key=value"
    )
    args = parser.parse_args()
    cfg = inputs.load(args.set)
    seed = (
        args.seed
        if args.seed is not None
        else int(cast(int, np.random.SeedSequence().entropy) % 2**32)
    )
    missing = inputs.refuse(cfg) + table.variants(cfg)[1]
    if not (args.paths or args.days):
        missing.append(
            "--paths <archivo.npz> o --days <tabla.parquet>: los caminos sobre los que se simula"
        )
    if missing:
        sys.exit(
            "No simulo: faltan decisiones tuyas o datos que el catálogo no trae. Dalos con "
            "--set <clave>=<valor>:\n  " + "\n  ".join(missing)
        )
    paths, meta = inputs.paths(args.paths) if args.paths else generated(args, seed)
    ledger = {"study": args.study, "symbol": args.symbol, "segment": args.segment}
    if not meta["synthetic"] and None in ledger.values():
        sys.exit(
            "No simulo: estos caminos salen de datos reales y la búsqueda cuenta en el ledger. "
            "Faltan --study, --symbol y --segment."
        )
    out = (
        args.out
        or portfolio_dir() / "bank" / f"{datetime.now():%Y%m%d_%H%M%S}_{meta['label']}"
    )
    zero = inputs.paths(args.monkey)[0] if args.monkey else None
    done = run(paths, meta, cfg, out, seed, zero, ledger)
    owner = cfg["owner"]
    print(
        f"\nCaja del fondeo — caminos «{meta['label']}»{' (SINTÉTICOS)' if meta['synthetic'] else ''}: "
        f"{paths['closed'].shape[0]} × {paths['closed'].shape[1]} días · recorte que ordena h = "
        f"{owner['haircut_decides']:g} · caja {owner['budget_eur']:g} € a {owner['eurusd']:g} $/€ · "
        f"{len(done['search'])} configuraciones\n"
    )
    print("\n".join(report.lines(done, owner)))
    print("\n" + report.sentence(done, owner))
    print("\nSin confirmar (se usa la lectura del catálogo o el supuesto dicho):")
    for key, f in done["flags"].items():
        print(f"  {key} [{f['status']}] — {', '.join(sorted(f['plans']))}")
    left = sorted({s for sets in done["skipped"].values() for s in sets})
    print(
        f"\nAdd-ons sin efecto en la simulación (sólo precio), no evaluados: {', '.join(left) or 'ninguno'}"
    )
    print(
        f"VE en USD por banco sobre el horizonte; [90 %] es el error de Monte Carlo del VE/mes; e.t. = error "
        f"típico de Monte Carlo del VE. El «mono» es el mejor riesgo del mono; h = 100% es el mono al riesgo "
        f"elegido con h = {owner['haircut_decides']:g}, por eso nunca lo supera. "
        f"Semilla {seed}. Resultado en {out}"
    )


if __name__ == "__main__":
    main()
