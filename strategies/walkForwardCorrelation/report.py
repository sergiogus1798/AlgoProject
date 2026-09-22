#!/usr/bin/env python3
"""The walk forward correlation of one strategy's parameter grid, as a page and a verdict."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from strategies.walkForwardCorrelation import measure, render

HERE = Path(__file__).resolve().parent
PAGE = """<!doctype html><meta charset="utf-8"><title>{title} — WFC</title>
<style>body{{margin:0;padding:32px;background:#f6f7f9;color:#14181f;
font:15px/1.6 Inter,system-ui,sans-serif}}main{{max-width:940px;margin:0 auto}}
figure{{margin:0 0 28px;background:#fff;border:1px solid #e3e7ec;border-radius:10px;
padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.call{{display:inline-block;padding:4px 12px;border-radius:99px;font-weight:600;
background:{tint};color:{ink}}}
table{{border-collapse:collapse;width:100%;font-size:14px;background:#fff;
border:1px solid #e3e7ec;border-radius:10px;overflow:hidden}}
th,td{{padding:8px 12px;text-align:right;border-bottom:1px solid #eef1f4}}
th:first-child,td:first-child{{text-align:left}}th{{background:#f0f2f5;font-weight:600}}
p.note{{color:#5b6675}}</style>
<main><figure>{svg}</figure>
<p><span class="call">{call}</span> &nbsp;{why}</p>
<p class="note">{note}</p>
{table}</main>"""
TINT = {"fiable": ("#dafbe1", "#0a5d2a"), "no_fiable": ("#ffebe9", "#8b1a12"),
        "indeciso": ("#fff8c5", "#7a5c00"), "sin_dato": ("#eef1f4", "#5b6675")}


def settings() -> dict:
    """This study's tunables.

    Returns:
        The parsed config.yaml.
    """
    return yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))


def shown(kept: pd.DataFrame, ends: int) -> tuple[pd.DataFrame, int]:
    """The rows worth tabulating when the batch is too big to tabulate.

    Args:
        kept: The usable points, sorted by in-sample profit.
        ends: How many to keep from each end.

    Returns:
        The controls plus the best and worst in-sample rows, and how many were hidden.

        **The ends are the table that matters.** The question is whether the in-sample
        winners stayed winners, so the reader needs the top of the in-sample ranking and
        something to compare it against -- not a thousand rows nobody will scroll.
    """
    keep = pd.concat([kept.head(ends), kept.tail(ends),
                      kept[kept["stratum"].isin(["origin", "canary"])]])
    keep = keep[~keep.index.duplicated()].sort_values(measure.IS, ascending=False)
    return keep, len(kept) - len(keep)


def table(kept: pd.DataFrame, ends: int) -> str:
    """The points behind the figure, so the reader can check any of them.

    Args:
        kept: The usable points.
        ends: How many rows to keep from each end of the in-sample ranking.

    Returns:
        An HTML table. The figure is the argument; this is the evidence.
    """
    ordered = kept.sort_values(measure.IS, ascending=False)
    rows, hidden = shown(ordered, ends)
    cells = [f'<tr><td>{r["variant_id"]}</td><td>{r["stratum"]}</td>'
             f'<td>{r[measure.IS]:,.0f}</td><td>{r[measure.TRADES_IS]:,.0f}</td>'
             f'<td>{r[measure.OOS]:,.0f}</td><td>{r[measure.TRADES_OOS]:,.0f}</td></tr>'
             for _, r in rows.iterrows()]
    if hidden:
        # The gap goes where the rows were dropped from, so the ranking still reads as one
        # ordered list rather than two tables stacked.
        cells.insert(len(cells) // 2,
                     f'<tr><td colspan="6" style="text-align:center;color:#5b6675">'
                     f'… {hidden:,} combinaciones intermedias no listadas; están todas '
                     f'en metrics.parquet …</td></tr>')
    head = ("<tr><th>variante</th><th>estrato</th><th>neto IS</th><th>ops IS</th>"
            "<th>neto OOS</th><th>ops OOS</th></tr>")
    return f"<table>{head}{''.join(cells)}</table>"


def main() -> None:
    """Measure the grid, draw it, and say what it licenses."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds metrics.parquet (contract C3)")
    a = ap.parse_args()

    cfg = settings()
    print("PROGRESS 20 leyendo el panel IS/OOS", flush=True)
    metrics = pd.read_parquet(a.work / "metrics.parquet")
    kept = measure.points(metrics, cfg["min_trades"])
    dropped = len(metrics) - len(kept)

    print(f"PROGRESS 55 {len(kept)} puntos utiles de {len(metrics)}", flush=True)
    found = measure.correlation(kept)
    said = measure.verdict(found, cfg["rho_floor"])

    title = a.work.name.replace("_", " ")
    tint, ink = TINT[said["call"]]
    note = (f"{dropped} de {len(metrics)} combinaciones descartadas por operar menos de "
            f"{cfg['min_trades']} veces en alguna de las dos muestras. Una combinacion que "
            f"apenas opera da un beneficio que mide una o dos operaciones, y sobre una "
            f"docena de puntos esas dominan la correlacion.")
    (a.work / "wfc.html").write_text(
        PAGE.format(title=title, svg=render.scatter(kept, found, said, title),
                    call=said["call"].replace("_", " "), why=said["why"], note=note,
                    table=table(kept, cfg["table_ends"]), tint=tint, ink=ink), encoding="utf-8")
    (a.work / "wfc.json").write_text(
        json.dumps({**found, **said, "dropped": dropped}, indent=2), encoding="utf-8")

    print(f"PROGRESS 100 rho {found['rho']:.2f} — {said['call']}", flush=True)
    print(f"\n{said['why']}\n-> {a.work / 'wfc.html'}")


if __name__ == "__main__":
    main()
