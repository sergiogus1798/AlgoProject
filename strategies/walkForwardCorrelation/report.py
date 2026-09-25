#!/usr/bin/env python3
"""The walk forward correlation of one strategy's parameter grid, as a page and a verdict."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from strategies.walkForwardCorrelation.inputs import config
from strategies.walkForwardCorrelation.measure import correlation
from strategies.walkForwardCorrelation.render.scatter import scatter

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


def shown(kept: pd.DataFrame, ends: int, cols: dict) -> tuple[pd.DataFrame, int]:
    """The rows worth tabulating when the batch is too big to tabulate.

    Args:
        kept: The usable points, sorted by in-sample profit.
        ends: How many to keep from each end.
        cols: What `correlation.columns` returned.

    Returns:
        The controls plus the best and worst in-sample rows, and how many were hidden.

        **The ends are the table that matters.** The question is whether the in-sample
        winners stayed winners, so the reader needs the top of the in-sample ranking and
        something to compare it against -- not a thousand rows nobody will scroll.
    """
    keep = pd.concat([kept.head(ends), kept.tail(ends),
                      kept[kept["stratum"].isin(["origin", "canary"])]])
    keep = keep[~keep.index.duplicated()].sort_values(cols["is"], ascending=False)
    return keep, len(kept) - len(keep)


def table(kept: pd.DataFrame, ends: int, cols: dict) -> str:
    """The points behind the figure, so the reader can check any of them.

    Args:
        kept: The usable points.
        ends: How many rows to keep from each end of the in-sample ranking.
        cols: What `correlation.columns` returned.

    Returns:
        An HTML table. The figure is the argument; this is the evidence.
    """
    ordered = kept.sort_values(cols["is"], ascending=False)
    rows, hidden = shown(ordered, ends, cols)
    cells = [f'<tr><td>{r["variant_id"]}</td><td>{r["stratum"]}</td>'
             f'<td>{r[cols["is"]]:,.0f}</td><td>{r[cols["trades_is"]]:,.0f}</td>'
             f'<td>{r[cols["oos"]]:,.0f}</td><td>{r[cols["trades_oos"]]:,.0f}</td></tr>'
             for _, r in rows.iterrows()]
    if hidden:
        # The gap goes where the rows were dropped from, so the ranking still reads as one
        # ordered list rather than two tables stacked.
        cells.insert(len(cells) // 2,
                     f'<tr><td colspan="6" style="text-align:center;color:#5b6675">'
                     f'… {hidden:,} combinaciones intermedias no listadas; están todas '
                     f'en metrics.parquet …</td></tr>')
    head = (f"<tr><th>variante</th><th>estrato</th><th>neto {cols['is_label']}</th>"
            f"<th>ops</th><th>neto {cols['oos_label']}</th><th>ops</th></tr>")
    return f"<table>{head}{''.join(cells)}</table>"


def main() -> None:
    """Measure the grid, draw it, and say what it licenses."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds metrics.parquet (contract C3)")
    ap.add_argument("--split", choices=sorted(correlation.MODES),
                    help="que se considera fuera de muestra. Por defecto, config.yaml: "
                         "`oos1_oos2` = IS build, OOS oos1+oos2; `oos2_only` = IS "
                         "build+oos1, OOS solo oos2, la lectura estricta")
    a = ap.parse_args()

    cfg = config.load()
    mode = a.split or cfg["split_mode"]
    cols = correlation.columns(mode)
    print(f"PROGRESS 20 leyendo el panel: IS={cols['is_label']}, OOS={cols['oos_label']}",
          flush=True)
    metrics = pd.read_parquet(a.work / "metrics.parquet")
    kept = correlation.points(metrics, cfg["min_trades"], cols)
    dropped = len(metrics) - len(kept)

    print(f"PROGRESS 55 {len(kept)} puntos utiles de {len(metrics)}", flush=True)
    found = correlation.correlation(kept, cols)
    said = correlation.verdict(found, cfg["rho_floor"])

    title = f"{a.work.name.replace('_', ' ')} — {cols['is_label']} vs {cols['oos_label']}"
    tint, ink = TINT[said["call"]]
    thin = json.loads((a.work / "collected.json").read_text(encoding="utf-8"))
    note = (f"{dropped} de {len(metrics)} combinaciones descartadas por operar menos de "
            f"{cfg['min_trades']} veces en alguna de las dos muestras "
            f"({cols['is_label']} o {cols['oos_label']}). Antes de eso, "
            f"{thin.get('thin', 0)} variantes ya habian quedado fuera del panel por no "
            f"llegar a {thin.get('floor', '?')} operaciones en todo el periodo. Una "
            f"combinacion que apenas opera da un beneficio que mide una o dos "
            f"operaciones, y sobre una docena de puntos esas dominan la correlacion.")
    (a.work / "wfc.html").write_text(
        PAGE.format(title=title, svg=scatter(kept, found, said, title, cols),
                    call=said["call"].replace("_", " "), why=said["why"], note=note,
                    table=table(kept, cfg["table_ends"], cols), tint=tint, ink=ink),
        encoding="utf-8")
    (a.work / "wfc.json").write_text(
        json.dumps({**found, **said, "dropped": dropped,
                    "dropped_thin": thin.get("thin", 0), "split_mode": mode,
                    "in_sample": cols["is_label"], "out_of_sample": cols["oos_label"]},
                   indent=2), encoding="utf-8")

    print(f"PROGRESS 100 rho {found['rho']:.2f} — {said['call']} "
          f"({len(kept)} puntos; {thin.get('thin', 0)} fuera por pocas operaciones en "
          f"total, {dropped} por pocas en un lado)", flush=True)
    print(f"\n{said['why']}\n-> {a.work / 'wfc.html'}")


if __name__ == "__main__":
    main()
