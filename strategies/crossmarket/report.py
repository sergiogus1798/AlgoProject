#!/usr/bin/env python3
"""Run the cross-market study over a retest export and write the per-market rows and verdict."""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from core import bars, manifest, trades
from core.paths import bars_file, export_dir, report_dir
from strategies.crossmarket import backtest, inference, markets, panel, text, trade_models

DRAWS = 5000
VERDICT_MODEL = "block_shift"   # the only model that randomises exactly one thing


def market_rows(feed: str, folder: Path, price: pd.DataFrame, draws: int,
                models: list[str]) -> tuple[list[dict], dict]:
    """Every strategy's row on one market, one column of p-values per model.

    Args:
        feed: SQX symbol of the market.
        folder: Directory of that market's per-strategy trade CSVs.
        price: That market's bars.
        draws: Random runs per model.
        models: Keys of trade_models.MODELS, the verdict's model first.

    Returns:
        One row per strategy and the null distributions of the verdict's model, keyed
        "<strategy>|<market>". The verdict model's p-value is `p`; the others are `p_<model>`,
        so a disagreement between models is visible in the same row rather than in two reports.
    """
    rows, shapes = [], {}
    for f in sorted(folder.glob("*.csv")):
        real = trades.read(f)
        row = {"strategy": f.stem, "market": feed}
        for model in models:
            out = backtest.run(real, price, draws, model)
            located = inference.locate(out["real"], out["null"])
            suffix = "" if model == models[0] else f"_{model}"
            row.update({f"p{suffix}": located["p"], f"edge_r{suffix}": located["edge_r"]})
            if model == models[0]:
                row.update({k: v for k, v in out.items() if k not in ("null", "real")},
                           real_r=out["real"], null_r=located["null_r"],
                           resolution=located["resolution"])
                shapes[f"{f.stem}|{feed}"] = inference.shape(out["real"], out["null"])
        row["testable"] = inference.testable(row)
        rows.append(row)
    return rows, shapes


def page(a: argparse.Namespace, rows: pd.DataFrame, calls: pd.DataFrame, luck: dict,
         shapes: dict) -> str:
    """The illustrated report, in reading order.

    Args:
        a: Parsed command line.
        rows: Every (strategy, market) row.
        calls: One row per strategy.
        luck: Expected false passes.
        shapes: The null distributions to draw.

    Returns:
        A self-contained HTML page. It opens with the verdict and the luck figure, because a
        page of histograms invites the reader to believe the histograms.
    """
    title = f"Retest en mercados adicionales — {a.project} / {a.databank}"
    return panel.render(title, [
        f"<h1>{title}</h1>",
        f'<p class="lede">Activo base <code>{a.asset}</code> · {a.draws} backtests aleatorios '
        f'por modelo · export {a.export}. El p-valor más pequeño observable es '
        f'{1 / (1 + a.draws):.5f}.</p>',
        panel.headline(rows, calls, luck),
        panel.luck_note(calls, luck),
        "<h2>Por mercado</h2>", panel.market_table(rows),
        "<h2>Estrategia a estrategia</h2>",
        '<p class="lede">Las barras son los 5.000 backtests aleatorios; la línea naranja es el '
        'backtest real. Cuanto más a la derecha de la masa azul, más difícil es explicarlo por '
        'azar.</p>',
        panel.per_strategy(rows, shapes, a.models),
        "<h2>Comprobaciones</h2>",
        '<p class="lede">Si alguna de estas falla, el resto de la página no significa nada.</p>',
        panel.diagnostics(rows),
        panel.glossary(a.models),
        f"<footer>{a.project} / {a.databank} · semilla {backtest.SEED} · "
        f"generado por <code>strategies.crossmarket.report</code></footer>"])


def main() -> None:
    """Read a retest export, test every strategy on every additional market, write the report."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank export_retest exported")
    ap.add_argument("--asset", required=True, help="base asset, e.g. XAUUSD")
    ap.add_argument("--export", required=True, help="export date, YYYY-MM-DD")
    ap.add_argument("--draws", type=int, default=DRAWS)
    ap.add_argument("--models", nargs="+", default=[VERDICT_MODEL, "segment_permute"],
                    choices=list(trade_models.MODELS), help="first one decides the verdict")
    a = ap.parse_args()

    spec = markets.load(a.asset)
    source = export_dir(a.project, a.databank, a.export) / "trades"

    rows, shapes = [], {}
    for market in spec["additional"]:
        feed = market["feed"]
        price = bars.read(bars_file(feed, spec["timeframe"]))
        found, drawn = market_rows(feed, source / feed, price, a.draws, a.models)
        rows.extend(found)
        shapes.update(drawn)
        print(f"{feed:30} {len(found):>5} strategies")

    per_market = pd.DataFrame(rows)
    calls = inference.table(per_market)
    # Median over every strategy, not only the judged ones: a retest with fewer additional
    # markets than the vote needs leaves nothing judged, and the luck figure still has to say
    # what that many markets would have been worth.
    luck = inference.false_passes(int(calls["markets"].median()), len(calls))

    out = report_dir(a.project, a.databank, date.today().isoformat()) / "crossmarket"
    out.mkdir(parents=True, exist_ok=True)
    per_market.to_csv(out / "by_market.csv", index=False)
    calls.to_csv(out / "verdict.csv", index=False)
    (out / "crossmarket.md").write_text(
        text.render(a, spec, per_market, calls, luck), encoding="utf-8")
    (out / "crossmarket.html").write_text(page(a, per_market, calls, luck, shapes),
                                          encoding="utf-8")
    manifest.write(out,
                   {"project": a.project, "databank": a.databank, "asset": a.asset,
                    "export": a.export, "draws": a.draws, "seed": backtest.SEED,
                    "models": a.models},
                   f"strategies.crossmarket.report --project {a.project} "
                   f"--databank {a.databank} --asset {a.asset} --export {a.export}",
                   {"strategies": len(calls), "markets": len(spec["additional"]),
                    **calls.verdict.value_counts().to_dict()})
    print(f"{len(calls)} estrategias → {out}")


if __name__ == "__main__":
    main()
