#!/usr/bin/env python3
"""The batch half of the cross-market study: every strategy of one export, to a verdict table."""

import argparse
import csv
import os
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

from core import barstore, tradestore
from core.paths import export_dir, report_dir

from strategies.crossmarket.explorer import analysis
from strategies.crossmarket.inputs import config, markets

COLUMNS = ["strategy", "verdict", "reason", "markets", "cleared", "fraction",
           "under_alpha", "paired_under_alpha", "edge_r", "worst_pf", "pf_cv",
           "family", "missing", "warnings"]


def judge(summary: dict, floor: float) -> tuple[str, str]:
    """Whether a strategy's edge showed up on the markets it never saw.

    Args:
        summary: The `summary` block of one `analyse_strategy` record.
        floor: Fraction of markets whose expectancy interval must clear zero.

    Returns:
        (verdict, reason). DESCARTAR is what `/curate` acts on; everything else is kept.

    One screen and one number, deliberately: breadth is the only reading of this study that
    does not need a model to be believed — an expectancy interval clearing zero on a market
    the strategy was never fitted to is arithmetic. The p-values are reported beside it and
    decide nothing, because they come from a placement model and the owner reads the model
    before he reads its p.
    """
    got = summary["fraction"]
    if got >= floor:
        return "MANTENER", (f"{summary['cleared']} de {summary['markets']} mercados con la "
                            f"esperanza por encima de cero ({got:.0%} >= {floor:.0%})")
    return "DESCARTAR", (f"solo {summary['cleared']} de {summary['markets']} mercados con la "
                         f"esperanza por encima de cero ({got:.0%} < {floor:.0%})")


def row(name: str, record: dict, floor: float) -> dict:
    """One strategy's line of the table.

    Args:
        name: Strategy name, exactly as SQX has it.
        record: What `analysis.analyse_strategy` returned.
        floor: The breadth floor the verdict is taken against.

    Returns:
        A dict with every column of COLUMNS.
    """
    got = record["summary"]
    verdict, reason = judge(got, floor)
    return {"strategy": name, "verdict": verdict, "reason": reason,
            "markets": got["markets"], "cleared": got["cleared"],
            "fraction": round(got["fraction"], 4),
            "under_alpha": got["under_alpha"], "paired_under_alpha": got["paired_under_alpha"],
            "edge_r": round(got["edge_r"], 6), "worst_pf": round(got["worst_market"]["pf"], 4),
            "pf_cv": round(got["pf_cv"], 4), "family": got["family"],
            "missing": got["missing"], "warnings": got["warnings"]}


def setup(project: str, databank: str, asset: str, export: str, overrides: list[str]) -> dict:
    """Everything the study needs, assembled once for the whole export.

    Args:
        project: SQX project name.
        databank: Databank `export_retest` exported.
        asset: Base asset, e.g. "USDJPY".
        export: Export date, YYYY-MM-DD.
        overrides: config.yaml overrides, as KEY=VALUE.

    Returns:
        The same dict the panel builds, plus the strategy names. The whole export is one
        read: every view slices it with `tradestore.market` rather than opening a file per
        strategy and market.
    """
    packed = export_dir(project, databank, export) / "trades.parquet"
    universe = markets.universe(asset, packed)
    trades = tradestore.read(packed)
    names = sorted(trades.loc[trades["Symbol"] == universe["main"], "strategy"].unique())
    return {"project": project, "databank": databank, "export": export, "asset": asset,
            "universe": universe, "trades": trades, "strategies": names,
            "cfg": config.load(overrides),
            "bars": {feed: barstore.read(feed, universe["timeframe"])
                     for feed in markets.feeds(universe)}}


# What the workers read: the whole export and every feed's bars, which is gigabytes. Set
# once before the pool is built and never written again, so `fork` hands each worker the
# same pages instead of pickling them one per strategy.
_SHARED: dict = {}


def _one(name: str) -> dict:
    """One strategy's whole cross-market study, in a worker that inherited the export.

    Args:
        name: Strategy name, exactly as SQX has it.

    Returns:
        Its line of the table. Only the line comes back: `analyse_strategy` also returns
        every equity curve, every null run and the portfolio account, and returning those
        would cost more to pickle than the study costs to compute.
    """
    got, cfg, floor = _SHARED["got"], _SHARED["cfg"], _SHARED["floor"]
    record = analysis.analyse_strategy(got, cfg, name, None, lambda *_: None)
    return row(name, record, floor)


def main() -> None:
    """Run every strategy of one export and write the verdict table `/curate` applies."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank export_retest exported")
    ap.add_argument("--asset", required=True, help="base asset, e.g. USDJPY")
    ap.add_argument("--export", required=True, help="export date, YYYY-MM-DD")
    ap.add_argument("--floor", type=float, default=0.5,
                    help="fraction of markets whose expectancy must clear zero to keep it")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--workers", type=int, default=os.cpu_count(),
                    help="strategies studied at once; each holds its own null batches, so "
                         "this is the knob that trades RAM for wall clock")
    a = ap.parse_args()

    got = setup(a.project, a.databank, a.asset, a.export, a.set)
    feeds = {m["feed"] for m in got["universe"]["markets"]}
    traded = got["trades"][got["trades"]["Symbol"].isin(feeds)].groupby(
        "strategy", observed=True).size()
    print(f"{len(got['strategies'])} estrategias x {len(got['universe']['markets'])} mercados "
          f"a {config.load(a.set)['nulls']['draws']:,} sorteos — minutos por estrategia. "
          "Bájalos con --set nulls.draws=2000 para una prueba.", flush=True)
    # A strategy that never fired on a single one of the other markets has nothing to judge,
    # and judging it anyway is not a near miss: the per-market table comes back empty and
    # `inference.family` dies on it, taking the whole batch down. It is a result about the
    # strategy — the panel calls it `missing` — so it is written as one, and it never
    # reaches a worker.
    silent = {name: {**{c: "" for c in COLUMNS}, "strategy": name, "verdict": "DESCARTAR",
                     "markets": 0, "cleared": 0, "fraction": 0.0, "missing": len(feeds),
                     "reason": f"no disparó ni una vez en ninguno de los {len(feeds)} "
                               "mercados: no hay nada que juzgar"}
              for name in got["strategies"] if int(traded.get(name, 0)) == 0}
    wanted = [n for n in got["strategies"] if n not in silent]
    _SHARED.update(got=got, cfg=got["cfg"], floor=a.floor)
    # The strategies share no state and write nothing, so the outer loop is the whole
    # parallelism there is here — and it is the only one: the cost is operations x draws x
    # markets x models and every micro-optimisation inside it was measured and did not pay.
    # `fork` because the export is gigabytes; this is a batch command with no threads.
    workers = max(1, min(a.workers, len(wanted)))
    print(f"{workers} procesos en paralelo sobre {len(wanted)} estrategias "
          f"({len(silent)} sin disparo en ningún mercado ajeno)", flush=True)
    rows = list(silent.values())
    with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("fork")) as pool:
        for i, (name, line) in enumerate(zip(wanted, pool.map(_one, wanted, chunksize=1)), 1):
            rows.append(line)
            # Flushed: a batch that prints nothing until it finishes is indistinguishable
            # from one that hung.
            print(f"  [{i}/{len(wanted)}] {name:22} {line['verdict']:9} {line['reason']}",
                  flush=True)
    rows.sort(key=lambda r: got["strategies"].index(r["strategy"]))

    out = report_dir(a.project, a.databank, a.export) / "crossmarket"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "verdict.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    kept = sum(1 for r in rows if r["verdict"] != "DESCARTAR")
    print(f"\n{kept} de {len(rows)} pasan el suelo de amplitud -> {out / 'verdict.csv'}")
    print("⚠️ Un resultado guardado se puede leer como respuesta a una pregunta para la que no "
          "se calculó. Este CSV es la entrada de /curate, no el informe: el panel sigue siendo "
          "donde se mira una estrategia.")


if __name__ == "__main__":
    main()
