"""The path set of a funded run's chosen portfolio: its verdict's members, the Monte Carlo that decided stage B, the edge recentred on OOS."""

import argparse
import json
import sys
from pathlib import Path
from typing import cast

import numpy as np

from core.paths import portfolio_dir
from portfolio.common.construct.search.stageb_data import StageBData
from portfolio.funded.sim import haircut

FLAVOURS = ("D", "T1", "T2")


def draw(
    flavour: str,
    length: int,
    days: dict,
    units: list[dict],
    horizon: int,
    n_paths: int,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """One of stage B's three Monte Carlos at the bank's horizon."""
    from portfolio.common.construct.mc import (
        paths as mc_paths,
    )  # lazy: the engine is heavy

    if flavour == "D":
        return mc_paths.daily_blocks(days, horizon, n_paths, length, rng)
    if flavour == "T1":
        return mc_paths.trade_bootstrap(units, horizon, n_paths, rng)
    return mc_paths.trade_blocks(units, horizon, n_paths, length, rng)


def recentre(paths: dict[str, np.ndarray], level: float) -> dict[str, np.ndarray]:
    """The same paths with their edge (mean closed P&L per closing day) moved to `level`."""
    return haircut.apply(paths, 1.0 - level / haircut.edge(paths))


def build(
    run: Path,
    overrides: list[str],
    horizon: int,
    n_paths: int,
    edge_from: list[str],
    seed: int,
) -> tuple[dict[str, np.ndarray], dict]:
    """Draw the path set of the portfolio a funded run's verdict names.

    Args:
        run: A stage-A run folder that `funded_b` has judged (`verdict.json`).
        overrides: The `section.key=value` list the run was built under (its universe is keyed by it).
        horizon: Server days per draw — how long the bank is simulated.
        n_paths: Draws.
        edge_from: Calendar segments whose pooled edge the paths are recentred on (encargo 33
            §3.2: the level of the edge comes from OOS, never from the segment that chose).
        seed: Root of the draws.

    Returns:
        The five path arrays at unit risk, and the meta `inputs.paths` reads back: `unit_risk`,
        `days_per_year`, `label`, `synthetic` and `source` (run, pool, plan, members, the
        verdict's risk, pass and label, flavour, length, the build and OOS edges, `relaxed`,
        the ledger study and symbols).
    """
    from portfolio.common.construct import funded_b, funded_verdict
    from portfolio.common.construct.inputs import config
    from portfolio.common.construct.search import stageb_data, stageb_run

    judged = json.loads((run / "verdict.json").read_text(encoding="utf-8"))
    chosen, winner = judged["verdict"]["chosen"], judged["winner"]
    cfg, world = config.load(overrides), funded_b.load(run, overrides)
    members = chosen["members"]

    def days_of(segment: str) -> tuple[StageBData, dict[str, np.ndarray]]:
        """The members' data on one calendar segment, and their joint server-day table."""
        data = funded_verdict.prepare(world, members, world["calendar"][segment], cfg)
        return data, stageb_data.joint(
            data, stageb_run.rows_of(data, "+".join(members))
        )

    data, days = days_of("build")
    idx = stageb_run.rows_of(data, "+".join(members))
    paths = draw(
        winner["flavour"],
        int(winner["length"]),
        days,
        [data["units"][i] for i in idx],
        horizon,
        n_paths,
        np.random.default_rng(seed),
    )
    oos = [days_of(segment)[1]["closed"] for segment in edge_from]
    level = float(sum(c.sum() for c in oos) / sum(np.count_nonzero(c) for c in oos))
    built = haircut.edge(paths)
    span = (
        float(data["days"][-1] - data["days"][0]) / 86400e9
    )  # server days are midnights in ns
    handoff = json.loads(
        (run / "handoff" / "portfolio.json").read_text(encoding="utf-8")
    )
    source = {
        "run": str(run),
        "pool": world["pool_name"],
        "plan": world["plan"]["plan_key"],
        "members": members,
        "risk": chosen["risk"],
        "verdict_pass": judged["verdict"]["pass"],
        "verdict_label": judged["verdict"]["label"],
        "flavour": winner["flavour"],
        "length": int(winner["length"]),
        "edge_build": built,
        "edge_oos": level,
        "edge_from": edge_from,
        "seed": seed,
        "relaxed": judged.get("relaxed"),
        "study": handoff["ledger_study"],
        "symbol": "+".join(sorted({world["meta"][m]["symbol"] for m in members})),
    }
    meta = {
        "unit_risk": 1.0,
        "days_per_year": len(data["days"]) / (span / 365.25),
        "synthetic": False,
        "label": f"{run.name}_s{seed}",
        "source": source,
    }
    return recentre(paths, level), meta


def main() -> None:
    """Parse, draw, write the `.npz`, print what was drawn and the bank command that reads it."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument(
        "--run", type=Path, required=True, help="funded run folder with verdict.json"
    )
    parser.add_argument(
        "--horizon", type=int, required=True, help="server days per draw"
    )
    parser.add_argument("--n-paths", type=int, required=True, help="draws")
    parser.add_argument(
        "--edge-from",
        required=True,
        metavar="SEG[,SEG]",
        help="segments whose edge the paths are recentred on, e.g. oos1,oos2",
    )
    parser.add_argument("--seed", type=int, help="root of the draws; fresh when absent")
    parser.add_argument(
        "--out", type=Path, help="the .npz (default AlgoData/portfolio/bank/paths/…)"
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="section.key=value",
        help="the construct overrides the run was built under",
    )
    args = parser.parse_args()
    if not (args.run / "verdict.json").exists():
        sys.exit(
            f"No genero caminos: {args.run} no tiene verdict.json — la cartera fondeada sale del "
            f"veredicto (portfolio.common.construct.funded_b), no de aquí."
        )
    seed = (
        args.seed
        if args.seed is not None
        else int(cast(int, np.random.SeedSequence().entropy) % 2**32)
    )
    paths, meta = build(
        args.run, args.set, args.horizon, args.n_paths, args.edge_from.split(","), seed
    )
    src = meta["source"]
    out = args.out or portfolio_dir() / "bank" / "paths" / f"{meta['label']}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out,
        **paths,
        **{k: v for k, v in meta.items() if k != "source"},
        source=json.dumps(src, ensure_ascii=False),
    )
    print(
        f"Caminos de la cartera de {src['plan']} (K = {len(src['members'])}: "
        f"{', '.join(m[:8] for m in src['members'])}) — {args.n_paths} × {args.horizon} días, Monte Carlo "
        f"{src['flavour']}{'@' + str(src['length']) if src['length'] else ''} (el que decidió la etapa B), "
        f"semilla {seed}"
    )
    if src["relaxed"]:
        print(
            f"AJUSTADO: la cartera sale de una corrida con umbrales relajados {src['relaxed']} — no es un resultado"
        )
    print(f"Veredicto de la cartera: {src['verdict_label']}")
    print(
        f"Edge por día con cierre, a riesgo unidad: build {src['edge_build']:+.4f} → "
        f"{'+'.join(src['edge_from'])} {src['edge_oos']:+.4f} "
        f"({src['edge_oos'] / src['edge_build']:.0%} del de build); los caminos quedan centrados en el segundo"
    )
    if src["edge_oos"] <= 0:
        print(
            "AVISO: el edge fuera de muestra no es positivo — recortarlo con h lo ACERCA a cero; "
            "con esta cartera no hay edge que comprar."
        )
    print(
        f"Escrito en {out}\nLa caja: python3 -m portfolio.funded.sim.run --paths {out} --study {src['study']} "
        f"--symbol {src['symbol']} --segment {src['edge_from'][-1]} --set owner.eurusd=… …"
    )


if __name__ == "__main__":
    main()
