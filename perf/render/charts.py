"""The catalogue's figures, each with the sentence that says how to read it."""

import pandas as pd

from perf.render import svg

CAPTION = ('<figure class="fig"><figcaption><b>{title}</b><span>{how}</span></figcaption>'
           '{body}</figure>')


def figure(title: str, how: str, body: str) -> str:
    """One figure with its title and its reading instruction.

    Args:
        title: What the figure shows.
        how: How to read it, in one sentence. Never omitted: a figure nobody can read is
            decoration.
        body: The SVG.

    Returns:
        The finished block.
    """
    return CAPTION.format(title=title, how=how, body=body)


def drift(frame: pd.DataFrame) -> str:
    """Every target's cost over its measurement history, indexed to its first run.

    Args:
        frame: What store.history() returned.

    Returns:
        One line per target that has been measured at least twice, or a note saying there
        is no history yet.
    """
    series = {}
    for target, group in frame.groupby("target", sort=False):
        if len(group) < 2:
            continue
        per = group["wall_s"] / group["scale"]
        base = per.iloc[0]
        series[target] = list(enumerate(per / base * 100, start=1))
    if not series:
        return '<p class="lede">Aún no hay dos medidas del mismo objetivo que comparar.</p>'
    ticks = list(range(1, max(len(p) for p in series.values()) + 1))
    return figure(
        "Coste por unidad de trabajo, en % de la primera medida",
        "Cada línea es un objetivo. 100 es lo que costó la primera vez que se midió; 130 "
        "significa un 30 % más caro por operación, fila o fichero — no por corrida, así que "
        "un export que creció no aparece aquí como código más lento.",
        svg.curves(series, ticks, "%", zero=False))


def memory(frame: pd.DataFrame) -> str:
    """Peak resident memory of the newest measurement of each target.

    Args:
        frame: What store.history() returned.

    Returns:
        A bar per target, largest first.
    """
    last = frame.groupby("target", sort=False).last().reset_index()
    rows = sorted(((r.target, r.rss_peak_mb) for r in last.itertuples()),
                  key=lambda t: t[1], reverse=True)
    return figure(
        "Pico de memoria residente, árbol de procesos completo",
        "Incluye los trabajadores que el objetivo arranca, no sólo el proceso padre. Es la "
        "cifra que decide si una corrida cabe en la máquina: se mide muestreando cada 50 ms, "
        "así que un pico más corto que eso puede escapársele.",
        svg.hbars(rows, "MB", height=60 + 26 * len(rows)))


def ceiling(frame: pd.DataFrame) -> str:
    """The machine's scaling curves, cache-resident against DRAM-resident.

    Args:
        frame: What store.history(SCALING) returned, newest run only.

    Returns:
        Two curves over the worker counts.
    """
    if frame.empty:
        return '<p class="lede">El techo de la máquina no se ha medido todavía.</p>'
    last = frame[frame["day"] == frame["day"].max()]
    series = {kind: [(r.workers, r.gb_s) for r in last[last["kind"] == kind].itertuples()]
              for kind in ("cache", "dram")}
    ticks = sorted({x for points in series.values() for x, _ in points})
    return figure(
        "Lo que la máquina da cuando todos los núcleos piden memoria a la vez",
        "El mismo kernel moviendo los mismos bytes, cambiando sólo si el dato cabe en caché "
        "(cache) o hay que traerlo de la DRAM (dram). Si la línea dram se aplana y la cache "
        "sigue subiendo, los núcleos que sobran no están calculando: están esperando memoria.",
        svg.curves(series, ticks, "GB/s"))


def branches(rows: list[dict]) -> str:
    """Where the bytes of the data root sit.

    Args:
        rows: What disk.inventory.tree() returned.

    Returns:
        A bar per branch, the ten largest, in MB.
    """
    names = {r["branch"] for r in rows}
    leaves = [r for r in rows
              if not any(other.startswith(r["branch"] + "/") for other in names)]
    bars = [(r["branch"], r["bytes"] / 1e6) for r in leaves[:10]]
    return figure(
        "Dónde están los bytes de AlgoData",
        "Las diez ramas más grandes, en megabytes. Sólo las hojas: una rama que contiene a "
        "otra de la lista se omite, porque su barra sería la suma de sus hijas otra vez.",
        svg.hbars(bars, "MB", height=60 + 26 * len(bars)))


def formats(rows: list[dict]) -> str:
    """What each storage format costs to read back.

    Args:
        rows: What disk.formats.compare() returned.

    Returns:
        A bar per format and table, in milliseconds to read.
    """
    bars = [(f"{r['table']} · {r['format']}", r["read_s"] * 1000) for r in rows]
    return figure(
        "Coste de volver a leer la misma tabla, por formato",
        "Milisegundos para leer de disco la misma tabla real escrita de cuatro formas. Una "
        "tabla se escribe una vez y se lee en cada corrida, así que ésta es la columna que "
        "decide; el tamaño en disco está en la tabla de al lado.",
        svg.hbars(bars, "ms", height=60 + 26 * len(bars)))
