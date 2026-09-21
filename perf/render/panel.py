"""Assemble the catalogue page: what it costs now, what it cost before, and what disk holds."""

import argparse
from pathlib import Path

import pandas as pd

from core.paths import perf_dir
from perf import store, verdict
from perf.disk import report as disk_report
from perf.inputs import config
from perf.render import charts

TEMPLATE = Path(__file__).with_name("page.html")
PAGE = "rendimiento.html"
MARK = {verdict.REGRESSION: "no", verdict.IMPROVEMENT: "ok", verdict.STEADY: "",
        verdict.NOISY: "", verdict.FIRST: ""}


def table(headers: list[str], rows: list[list[str]]) -> str:
    """One table, first column a label and the rest numbers.

    Args:
        headers: Column titles.
        rows: Already-formatted cells.

    Returns:
        A scrollable table.
    """
    head = "".join(f'<th class="n">{h}</th>' if i else f"<th>{h}</th>"
                   for i, h in enumerate(headers))
    body = "".join("<tr>" + "".join(f'<td class="n">{c}</td>' if i else f"<td>{c}</td>"
                                    for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def headline(frame: pd.DataFrame, judged: pd.DataFrame, disk: pd.DataFrame) -> str:
    """The four numbers the page opens with.

    Args:
        frame: What store.history() returned.
        judged: What verdict.compare() returned.
        disk: The newest disk inventory.

    Returns:
        The stat row.
    """
    last = frame.iloc[-1]
    bytes_total = disk[~disk["branch"].str.contains("/")]["bytes"].sum() if len(disk) else 0
    stats = [(f"{len(judged)}", "objetivos en el catálogo"),
             (f"{int((judged['verdict'] == verdict.REGRESSION).sum())}", "regresiones"),
             (f"{bytes_total / 1e9:.2f} GB", "en el raíz de datos"),
             (f"{last['day']}", f"última medida · {last['commit']}")]
    return '<div class="headline">' + "".join(
        f"<div class='stat'><b>{v}</b><span>{k}</span></div>" for v, k in stats) + "</div>"


def costs(frame: pd.DataFrame, judged: pd.DataFrame) -> str:
    """The per-target table: what it costs now and how that moved.

    Args:
        frame: What store.history() returned.
        judged: What verdict.compare() returned.

    Returns:
        The section.
    """
    last = frame.groupby("target", sort=False).last()
    rows = []
    for r in judged.itertuples():
        row = last.loc[r.target]
        per = row["wall_s"] / row["scale"] * 1e6
        rows.append([r.target, f"{row['wall_s']:.2f}", f"{per:,.1f}",
                     f"{row['scale']:,.0f} {row['unit']}", f"{row['rss_peak_mb']:,.0f}",
                     f"{row['wall_spread_pct']:.1f}",
                     f'<span class="{MARK[r.verdict]}">{r.verdict}</span>'])
    return table(["objetivo", "segundos", "microsegundos/unidad", "trabajo", "MB pico", "dispersión %",
                  "veredicto"], rows)


def disk_tables(disk: pd.DataFrame, copies: pd.DataFrame, kinds: pd.DataFrame) -> str:
    """Branches, duplicates and formats, each as a table.

    Args:
        disk: Newest inventory rows.
        copies: Newest duplicate groups.
        kinds: Newest format comparison.

    Returns:
        The three tables with their headings.
    """
    stale = disk[disk["stale"]].head(10)
    out = ["<h3>Ramas sin tocar desde hace tiempo</h3>",
           table(["rama", "MB", "ficheros", "días"],
                 [[r.branch, f"{r.bytes / 1e6:,.1f}", f"{r.files:,}", f"{r.age_days:.0f}"]
                  for r in stale.itertuples()]) if len(stale) else
           '<p class="lede">Ninguna rama pasa del límite de antigüedad.</p>']
    if len(copies):
        out += ["<h3>Ficheros duplicados</h3>",
                table(["copias", "MB desperdiciados", "rutas"],
                      [[f"x{r.copies}", f"{r.wasted / 1e6:,.1f}", r.paths]
                       for r in copies.itertuples()])]
    if len(kinds):
        out += ["<h3>Formato: tamaño y coste de lectura</h3>",
                table(["tabla · formato", "MB", "escribir ms", "leer ms"],
                      [[f"{r.table} · {r.format}", f"{r.bytes / 1e6:,.2f}",
                        f"{r.write_s * 1000:,.0f}", f"{r.read_s * 1000:,.0f}"]
                       for r in kinds.itertuples()])]
    return "".join(out)


def _newest(name: str) -> pd.DataFrame:
    """The most recent day's rows of one catalogue file.

    Args:
        name: File name under the perf directory.

    Returns:
        The rows of its last run, or an empty frame when the file does not exist yet. The
        last run, not the last day: the inventory is often taken twice in an afternoon, and
        showing both would double every row.
    """
    frame = store.history(name)
    if not len(frame):
        return frame
    stamp = frame[["day", "time"]].iloc[-1]
    return frame[(frame["day"] == stamp["day"]) & (frame["time"] == stamp["time"])]


def build(cfg: dict) -> str:
    """The whole page.

    Args:
        cfg: What config.load() returned.

    Returns:
        Self-contained HTML: no scripts, no fonts, no network.
    """
    frame = store.history()
    judged = verdict.compare(frame, cfg)
    disk = _newest(disk_report.BRANCHES)
    body = [
        "<h1>Catálogo de rendimiento</h1>",
        '<p class="lede">Lo que cuesta hoy cada parte cara del proyecto, en tiempo y en '
        'memoria, comparado con lo que costaba la última vez que se midió.</p>',
        headline(frame, judged, disk),
        "<h2>Qué se movió</h2>", costs(frame, judged), charts.drift(frame),
        '<div class="note"><b>Cómo se decide que algo es una regresión.</b> Se compara el '
        f'tiempo <b>por unidad de trabajo</b> con la medida anterior. Por encima de '
        f'{cfg["regression"]["wall_pct"]} % es regresión; por debajo, si el cambio es menor '
        'que la dispersión entre repeticiones de la propia medida, se llama <i>noisy</i> en '
        'vez de <i>steady</i>: la medición no puede ver una diferencia de ese tamaño.</div>',
        "<h2>Memoria</h2>", charts.memory(frame),
        "<h2>El techo de la máquina</h2>", charts.ceiling(store.history("scaling.csv")),
        "<h2>AlgoData en disco</h2>", charts.branches(disk.to_dict("records")),
        disk_tables(disk, _newest(disk_report.COPIES), _newest(disk_report.FORMATS)),
        charts.formats(_newest(disk_report.FORMATS).to_dict("records"))
        if len(_newest(disk_report.FORMATS)) else "",
        "<footer>Generado por <code>python3 -m perf.render.panel</code>. Cada fila viene de "
        "<code>history.csv</code> en el raíz de datos, que sólo crece.</footer>"]
    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", "Rendimiento — AlgoProject").replace("__BODY__", "".join(body)))


def main() -> None:
    """Render the catalogue page and say where it landed."""
    ap = argparse.ArgumentParser(description="Render the performance catalogue page.")
    ap.add_argument("--set", action="append", default=[], help="config override, dotted.key=value")
    a = ap.parse_args()
    where = perf_dir() / PAGE
    where.write_text(build(config.load(a.set)), encoding="utf-8")
    print(where)


if __name__ == "__main__":
    main()
