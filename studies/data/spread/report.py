#!/usr/bin/env python3
"""Step 8's spread repricing: every strategy of a harvest with SQX's flat spread swapped for Darwinex's real one.

Reads a `studies.screening.gate.harvest` folder, the spread each task charged (from the project's
own `project.cfx`), and what step 4's `studies.data.spread.scan` left for the asset — the
reconstructed daily spread and the intraday shape. Keeps every trade three times side by side in
`trades.parquet`: SQX's P/L, at the real spread, and at the real spread plus a slippage that
follows it. Runs after `gate.report` on the same harvest,
as edgeCost and feedQuality do, and writes verdict.csv for /curate. The cheap stand-in for a
DATATICK retest on Darwinex: only the spread differs, so it is exact where the ticks exist.
"""

import argparse
from datetime import date

import pandas as pd

from core import assetdata, fanout
from core.datapaths import spread_dir
from core.paths import report_dir
from core.study import output, verdicts
from core.study.render import markdown
from core.study.result import progress
from studies.data.spread import inputs, many, one, reprice


# 🔬 2026-10-01, 5,130 strategies: `one.run` once each in one thread was 80 of the study's
# 110 s, and the population reads only each one's `summary`.
WORKERS = 8
_JOB: dict = {}      # what `_summary` reads, set before the fork


def _summary(identity: str) -> dict:
    """One strategy's `summary` row, in a worker: the rest of its reading stays there."""
    j = _JOB
    return one.run(j["names"][identity], identity, j["groups"][identity], j["charged"],
                   j["tick"], j["cfg"])["summary"]


def main() -> None:
    """Every strategy of one harvest at the real spread, or one read in full."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the harvest's build databank name")
    ap.add_argument("--feed", required=True, help="the feed the strategies were built on, e.g. XAUUSD_M1")
    ap.add_argument("--strategy", default="", help="one strategy, read in full; all when omitted")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    symbol = assetdata.symbol_for(a.feed)
    ticks = cfg["assets"][symbol]["ticks"]
    data = inputs.asset(symbol)
    folder = inputs.harvest(a.project, a.databank)
    scanned = spread_dir(ticks)
    daily = pd.read_parquet(scanned / "daily.parquet")
    hours = pd.read_parquet(scanned / "hours.parquet")["multiplier"]
    progress(5, "ticks")
    trades = inputs.trades(folder)
    charged, slippage = inputs.charged(folder, a.feed), inputs.slippage(folder, a.feed)
    paid = reprice.paid(trades, inputs.minutes(ticks), daily, hours, cfg["reprice"]["near_minutes"])
    point_value = data["instrument"]["point_value"]
    adjusted = reprice.adjust(trades, paid, charged, point_value)
    trades = trades.join(paid).assign(
        adjusted=adjusted, slipped=reprice.slip(trades, paid, adjusted, slippage, point_value))
    names = inputs.names(folder)
    wanted = names[names == a.strategy].index if a.strategy else names.index
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "spread"
    tick = data["instrument"]["tick_size"]

    groups = dict(tuple(trades.groupby("identity", observed=True)))
    todo = [i for i in wanted if i in groups]
    _JOB.update(names=names, groups=groups, charged=charged, tick=tick, cfg=cfg)
    if a.strategy:
        results = {i: one.run(names[i], i, groups[i], charged, tick, cfg) for i in todo}
    else:
        landed = {}
        for n, (identity, row) in enumerate(fanout.run(
                _summary, {i: len(groups[i]) for i in todo}, WORKERS)):
            landed[identity] = {"summary": row}
            progress(10 + 90 * (n + 1) // len(wanted), names[identity])
        results = {i: landed[i] for i in todo}      # the panel's order is the harvest's

    if a.strategy:
        got = results[wanted[0]]
        title = f"Spread real — {a.strategy}"
        print(markdown.render(got, title))
        page = output.member(out, got, title, f'{a.feed}, ticks de {ticks}.')
        mine = reprice.stored(trades[trades["identity"] == wanted[0]], charged, names)
        mine.to_parquet(page.with_name(f"{a.strategy}.trades.parquet"), index=False)
        print(f"-> {page}")
        return
    got = many.run(results, names, cfg)
    output.population(out, "spread", got["population"], f"Spread real — {a.project} / {a.databank}")
    reprice.stored(trades, charged, names).to_parquet(out / "trades.parquet", index=False)
    command = " ".join(["python3 -m studies.data.spread.report", "--project", a.project,
                        "--databank", a.databank, "--feed", a.feed, *a.set])
    verdicts.write(out, got["panel"].reset_index(), folder / "trades.parquet", command, a.set)
    print(f"{len(got['panel'])} estrategias, SQX cargó {charged}: "
          f"{got['population']['tabs'][0]['note']} -> {out}")


if __name__ == "__main__":
    main()
