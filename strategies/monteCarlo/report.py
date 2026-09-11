#!/usr/bin/env python3
"""Run the Monte Carlo study over every strategy of one databank and write its report."""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from core import assets, bars, manifest
from core.paths import bars_file, export_dir, report_dir
from strategies.monteCarlo import (config, costs, fan, panel, regime, run, scoring,
                                   stability, strategypage, stream, sweeps, text)

FAN_SIMS = 2000   # paths behind the equity cone; a picture of the spread, not a gate


def analyse_one(source: dict, day: pd.DataFrame, asset: dict, cfg: dict,
                shared: dict) -> tuple[dict, dict, str]:
    """Everything one strategy gets: the numbers, the verdict and its page.

    Args:
        source: What stream.build() or stream.portfolio() returned.
        day: Daily candles, from regime.daily().
        asset: What costs.load() returned.
        cfg: What config.load() returned.
        shared: What the appendix of every page shows: paths, costs, stability.

    Returns:
        The result, the verdict and the rendered page.
    """
    result = run.analyse(source, day, asset, cfg)
    verdict = scoring.verdict(result, cfg)
    band = fan.envelope(source["pnl"], "stationary",
                        config.stationary_block(source["pnl"].size), FAN_SIMS,
                        cfg["global"]["starting_equity"], [5, 25, 50, 75, 95])
    return result, verdict, strategypage.page(result, verdict, band, cfg, shared)


def page(a: argparse.Namespace, rows: pd.DataFrame, flags: pd.DataFrame, cfg: dict,
         shared: dict) -> str:
    """The databank page, in reading order.

    Args:
        a: Parsed command line.
        rows: One row per strategy.
        flags: One row per fired check.
        cfg: What config.load() returned.
        shared: What the appendix shows.

    Returns:
        A self-contained HTML page linking to every strategy's own report.
    """
    title = f"Monte Carlo — {a.project} / {a.databank}"
    return panel.render(title, [
        f"<h1>{title}</h1>",
        f'<p class="lede">{len(rows)} estrategias · {cfg["global"]["n_sims"]:,} simulaciones '
        f'por prueba · export {a.export}. Cada estrategia llega aquí ya con edge: esto mide de '
        f'qué depende, no si existe.</p>',
        panel.headline(rows),
        "<h2>Lo que falló</h2>",
        '<p class="lede">Cada prueba que vetó o avisó, cuántas estrategias tumbó, y el número '
        'de una de ellas.</p>',
        panel.failures(flags),
        "<h2>Estrategia a estrategia</h2>",
        '<p class="lede">Pincha el nombre para ver su informe completo.</p>',
        panel.verdict_table(rows),
        "<h2>Datos y método</h2>", panel.method(a, cfg, shared["stability"], shared),
        panel.limits(cfg),
        f"<footer>{a.project} / {a.databank} · generado por "
        f"<code>strategies.monteCarlo.report</code> · sin semilla</footer>"])


def main() -> None:
    """Analyse a databank's exported trades and write the report beside them."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--asset", required=True, help="asset name in assets/, e.g. XAUUSD")
    ap.add_argument("--export", required=True, help="export date, YYYY-MM-DD")
    ap.add_argument("--bars-timeframe", default="M30",
                    help="which exported bars the daily volatility is built from")
    ap.add_argument("--portfolio", action="store_true",
                    help="treat every strategy as one combined trade stream")
    ap.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE",
                    help="override any config value, e.g. global.n_sims=20000")
    a = ap.parse_args()

    print(assets.report(a.asset))
    cfg = config.load(a.set)
    asset = costs.load(a.asset)
    source_dir = export_dir(a.project, a.databank, a.export) / "trades"
    files = sorted(source_dir.glob("*.csv"))
    first = stream.build(files[0], asset, cfg["global"]["risk_per_trade"])
    feed = str(first["frame"]["Symbol"].iloc[0])
    day = regime.daily(bars.read(bars_file(feed, a.bars_timeframe)))

    streams = ([stream.portfolio(files, asset, cfg["global"]["risk_per_trade"], a.databank)]
               if a.portfolio else
               [stream.build(f, asset, cfg["global"]["risk_per_trade"]) for f in files])
    reference = max(streams, key=lambda s: s["pnl"].size)
    print(f"{len(streams)} streams · estabilidad sobre {reference['name']}")
    shared = {"args": a, "export": source_dir, "bars": bars_file(feed, a.bars_timeframe),
              "cost": costs.crosscheck(reference["frame"], asset),
              "vol_model": cfg["family_d"]["vol_model"],
              "stability": stability.spread(reference, cfg)}

    # A portfolio run writes beside the per-strategy one, never over it: they answer
    # different questions about the same databank and both are worth keeping.
    out = (report_dir(a.project, a.databank, date.today().isoformat())
           / ("montecarlo_portfolio" if a.portfolio else "montecarlo"))
    (out / "estrategias").mkdir(parents=True, exist_ok=True)
    rows, fired = [], []
    for i, source in enumerate(streams, 1):
        print(f"[{i}/{len(streams)}] {source['name']}  ({source['pnl'].size} operaciones)")
        result, verdict, html = analyse_one(source, day, asset, cfg, shared)
        (out / "estrategias" / f"{source['name']}.html").write_text(html, encoding="utf-8")
        rows.append(text.row(result, verdict))
        fired += [{"strategy": source["name"], **f} for f in verdict["flags"]]
        print(f"    {verdict['tier']}  compuesto {verdict['composite']:.0f}  "
              f"{sum(1 for f in verdict['flags'] if f['gate'])} vetos")

    table = pd.DataFrame(rows)
    flags = pd.DataFrame(fired, columns=["strategy", "family", "test", "value", "limit",
                                         "gate"])
    table.to_csv(out / "verdict.csv", index=False)
    flags.to_csv(out / "flags.csv", index=False)
    (out / "montecarlo.md").write_text(
        text.markdown(a, table, flags, shared["stability"], cfg), encoding="utf-8")
    (out / "montecarlo.html").write_text(page(a, table, flags, cfg, shared),
                                         encoding="utf-8")
    manifest.write(out,
                   {"project": a.project, "databank": a.databank, "asset": a.asset,
                    "export": a.export, "bars": str(shared["bars"]),
                    "config": cfg, "portfolio": a.portfolio},
                   f"python3 -m strategies.monteCarlo.report --project {a.project} "
                   f"--databank {a.databank} --asset {a.asset} --export {a.export}",
                   {"strategies": len(table), "models": len(sweeps.plan(
                       reference["pnl"].size, cfg)),
                    **table.tier.value_counts().to_dict()})
    print(f"{len(table)} estrategias → {out}")


if __name__ == "__main__":
    main()
