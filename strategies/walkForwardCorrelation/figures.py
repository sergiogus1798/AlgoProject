"""The CSCV as a page: where the chosen variant landed, and what it cost to choose it."""

import numpy as np
import pandas as pd

W, ROW = 900, 170
PAD = {"l": 70, "r": 30, "t": 34, "b": 40}
INK, MUTED, GRID = "#14181f", "#5b6675", "#d8dde5"
GOOD, BAD = "#1a7f37", "#b3261e"
BINS = 41
CALL = {"primer_orden": "gana siempre", "segundo_orden": "gana en promedio",
        "ninguna": "no gana"}


def _bars(records: pd.DataFrame, top: float, base: float, span: tuple) -> str:
    """One rule's histogram of lambda, drawn inside its own band of the figure.

    Args:
        records: What `cscv.run` returned for that rule.
        top: Pixel of the band's top.
        base: Pixel of its baseline.
        span: (low, high) of lambda across every rule, so the bands share an axis.

    Returns:
        The bars, red left of zero and green right of it. Left of zero is the event the
        study counts: the parameter set that won in sample came back below average.
    """
    low, high = span
    counts, edges = np.histogram(records["lam"], bins=BINS, range=(low, high))
    wide = (W - PAD["l"] - PAD["r"]) / BINS
    tall = base - top
    out = []
    for n, count in enumerate(counts):
        if not count:
            continue
        height = count / counts.max() * tall
        x = PAD["l"] + n * wide
        hue = BAD if edges[n + 1] <= 0 else GOOD
        out.append(f'<rect x="{x:.1f}" y="{base - height:.1f}" width="{wide - 1:.1f}" '
                   f'height="{height:.1f}" fill="{hue}" opacity="0.85"/>')
    return "".join(out)


def lambdas(runs: dict, found: dict) -> str:
    """Every rule's distribution of lambda, one band each, on one shared axis.

    Args:
        runs: {rule: what `cscv.run` returned}.
        found: {rule: its summary}.

    Returns:
        An SVG. The whole argument of the study is readable here without a number: a
        distribution sitting left of the line is a way of choosing parameters that picks
        the ones about to disappoint, and the three bands say whether changing the rule
        moves it.
    """
    span = (min(r["lam"].min() for r in runs.values()),
            max(r["lam"].max() for r in runs.values()))
    span = (min(span[0], -0.5), max(span[1], 0.5))
    height = PAD["t"] + ROW * len(runs) + PAD["b"]
    zero = PAD["l"] + (0 - span[0]) / (span[1] - span[0]) * (W - PAD["l"] - PAD["r"])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
             f'width="100%" font-family="Inter,system-ui,sans-serif">',
             f'<text x="{PAD["l"]}" y="20" font-size="15" font-weight="600" fill="{INK}">'
             f'Cuantas veces lo elegido queda por debajo de la mediana</text>']
    for n, (name, records) in enumerate(runs.items()):
        top = PAD["t"] + ROW * n + 26
        base = PAD["t"] + ROW * (n + 1) - 14
        pbo = found[name]["pbo"]
        parts += [_bars(records, top, base, span),
                  f'<line x1="{PAD["l"]}" y1="{base}" x2="{W - PAD["r"]}" y2="{base}" '
                  f'stroke="{GRID}"/>',
                  f'<line x1="{zero:.1f}" y1="{top - 8}" x2="{zero:.1f}" y2="{base}" '
                  f'stroke="{INK}" stroke-width="2"/>',
                  f'<text x="{PAD["l"]}" y="{top - 12}" font-size="14" font-weight="600" '
                  f'fill="{INK}">{name}</text>',
                  f'<text x="{W - PAD["r"]}" y="{top - 12}" font-size="14" '
                  f'text-anchor="end" fill="{BAD if pbo > 0.5 else GOOD}" '
                  f'font-weight="600">PBO {pbo:.0%}</text>']
    parts += [f'<text x="{zero:.1f}" y="{height - 16}" font-size="12" '
              f'text-anchor="middle" fill="{MUTED}">0 = la mediana</text>',
              f'<text x="{PAD["l"]}" y="{height - 16}" font-size="12" fill="{MUTED}">'
              f'peor ({span[0]:.1f})</text>',
              f'<text x="{W - PAD["r"]}" y="{height - 16}" font-size="12" '
              f'text-anchor="end" fill="{MUTED}">mejor ({span[1]:.1f})</text>', "</svg>"]
    return "".join(parts)


def decay(records: pd.DataFrame, found: dict, name: str) -> str:
    """What each partition promised in sample against what it delivered out of it.

    Args:
        records: What `cscv.run` returned for one rule.
        found: That rule's summary.
        name: The rule, for the caption.

    Returns:
        An SVG, one dot per partition.

        ⚠️ **This line leans down even when nothing is wrong**, and the caption on the
        page says so. The two halves are complementary, so a partition whose winner
        looked unusually good inside has less left over outside. The figure is here to
        show the spread and the sign of the out-of-sample results, not to be read as a
        decay rate -- the number for that is `slope` in the table, fitted across all the
        variants instead of only the chosen one.
    """
    height = 420
    x, y = records["is_sharpe"].to_numpy(), records["oos_sharpe"].to_numpy()
    slope, intercept = np.polyfit(x, y, 1)
    both = np.concatenate([x, y])
    low, high = both.min(), both.max()
    pad = (high - low) * 0.08 or 0.1
    low, high = low - pad, high + pad

    def px(v: float) -> float:
        """Horizontal pixel of a Sharpe value.

        Args:
            v: The value.

        Returns:
            Its x coordinate.
        """
        return PAD["l"] + (v - low) / (high - low) * (W - PAD["l"] - PAD["r"])

    def py(v: float) -> float:
        """Vertical pixel of a Sharpe value, on the same scale as the horizontal one.

        Args:
            v: The value.

        Returns:
            Its y coordinate. Both axes share a scale so the diagonal means "kept it all".
        """
        return height - PAD["b"] - (v - low) / (high - low) * (height - PAD["t"] - PAD["b"])

    dots = "".join(f'<circle cx="{px(a):.1f}" cy="{py(b):.1f}" r="4" fill="#0969da" '
                   f'opacity="0.5"/>' for a, b in zip(x, y))
    fit = (f'<line x1="{px(low):.1f}" y1="{py(slope * low + intercept):.1f}" '
           f'x2="{px(high):.1f}" y2="{py(slope * high + intercept):.1f}" '
           f'stroke="{MUTED}" stroke-width="3" stroke-dasharray="7 4"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
            f'width="100%" font-family="Inter,system-ui,sans-serif">'
            f'<text x="{PAD["l"]}" y="20" font-size="15" font-weight="600" fill="{INK}">'
            f'Lo elegido por {name}, particion a particion</text>'
            f'<line x1="{px(low):.1f}" y1="{py(0):.1f}" x2="{px(high):.1f}" '
            f'y2="{py(0):.1f}" stroke="{GRID}"/>'
            f'<line x1="{px(0):.1f}" y1="{py(low):.1f}" x2="{px(0):.1f}" '
            f'y2="{py(high):.1f}" stroke="{GRID}"/>{dots}{fit}'
            f'<text x="{W - PAD["r"]}" y="{height - 14}" font-size="13" '
            f'text-anchor="end" fill="{MUTED}">Sharpe semanal dentro de muestra</text>'
            f'<text x="{PAD["l"] - 50}" y="{PAD["t"]}" font-size="13" fill="{MUTED}">'
            f'fuera</text></svg>')


def table(found: dict, result: dict) -> str:
    """Every number the page shows, with what it means in one sentence.

    Args:
        found: {rule: its summary and cost}.
        result: The flat result dictionary.

    Returns:
        An HTML table, one row per rule. The owner reads the figures first and this
        second; a statistic nobody can restate in a sentence should not be on the page.
    """
    head = ("<tr><th>regla</th><th>PBO</th><th>percentil OOS</th><th>IC 95 %</th>"
            "<th>pierde</th><th>vs. la mediana</th></tr>")
    rows = "".join(
        f'<tr><td>{name}</td>'
        f'<td class="{"bad" if f["pbo"] > 0.5 else "good"}">{f["pbo"]:.0%}</td>'
        f'<td>{f["pct_oos"]:.1f}</td><td>{f["ci95"][0]:.1f} a {f["ci95"][1]:.1f}</td>'
        f'<td>{f["prob_loss"]:.0%}</td>'
        f'<td>{CALL[f["dominance"]]}</td></tr>' for name, f in found.items())
    return f"<table>{head}{rows}</table>"


def page(title: str, runs: dict, found: dict, result: dict) -> str:
    """The whole report.

    Args:
        title: The batch's name.
        runs: {rule: what `cscv.run` returned}.
        found: {rule: its summary and cost}.
        result: The flat result dictionary.

    Returns:
        A standalone HTML page.
    """
    head = list(runs)[0]
    note = (f'{result["n"]} variantes, {result["periods"]} periodos de tipo '
            f'{result["period"]}, {result["blocks"]} bloques y '
            f'{found[head]["partitions"]} particiones. Las {result["n"]} variantes valen '
            f'{result["n_clusters"]} pruebas independientes una vez agrupadas por lo '
            f'parecido de sus rendimientos, y con ese recuento el Sharpe del mejor '
            f'sobrevive con probabilidad {result["dsr"]:.2f}. El mejor dentro de muestra '
            f'y el mejor fuera distan {result["levels_max"]} niveles en el parametro que '
            f'mas se movio. De una mitad a la otra el orden se conserva con pendiente '
            f'{result["slope"]:+.2f}: la tabla de arriba no la repite por regla porque '
            f'no depende de la regla, solo de la superficie.')
    return (f"<!doctype html><meta charset='utf-8'><title>{title} — CSCV</title>"
            "<style>body{margin:0;padding:32px;background:#f6f7f9;color:#14181f;"
            "font:15px/1.6 Inter,system-ui,sans-serif}main{max-width:940px;margin:0 auto}"
            "figure{margin:0 0 28px;background:#fff;border:1px solid #e3e7ec;"
            "border-radius:10px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.05)}"
            "table{border-collapse:collapse;width:100%;font-size:14px;background:#fff;"
            "border:1px solid #e3e7ec;border-radius:10px;overflow:hidden;margin-bottom:22px}"
            "th,td{padding:8px 12px;text-align:right;border-bottom:1px solid #eef1f4}"
            "th:first-child,td:first-child{text-align:left}th{background:#f0f2f5;"
            "font-weight:600}td.bad{color:#8b1a12;font-weight:600}"
            "td.good{color:#0a5d2a;font-weight:600}p.note{color:#5b6675}"
            "dt{font-weight:600;margin-top:10px}dd{margin:0;color:#5b6675}</style>"
            f"<main><figure>{lambdas(runs, found)}</figure>{table(found, result)}"
            f"<p class='note'>{note}</p>"
            f"<figure>{decay(runs[head], found[head], head)}</figure>"
            "<p class='note'>La recta de puntos de esa figura cae aunque no pase nada "
            "malo: las dos mitades son complementarias, asi que una particion cuyo "
            "ganador brillo dentro deja menos por ganar fuera. Sobre ruido puro esa "
            "recta marca -0,57. Lo que hay que leer es la columna pendiente de la "
            "tabla, que se ajusta sobre todas las variantes y sobre ruido marca 0.</p>"
            "<dl><dt>PBO</dt><dd>De cada 100 formas de partir la historia en dos mitades, "
            "en cuantas la combinacion elegida por la mitad de entrenamiento acabo por "
            "debajo de la mediana en la otra. Por encima del 50 % elegir asi es peor que "
            "no elegir.</dd>"
            "<dt>Percentil OOS</dt><dd>En que percentil del ranking real fuera de muestra "
            "cayo lo que la regla habria elegido. 50 es lo que da elegir a ciegas.</dd>"
            "<dt>Pendiente (en el parrafo)</dt><dd>Cuanto del orden dentro de muestra se "
            "conserva fuera, ajustado sobre TODAS las variantes de cada particion. 1 "
            "seria conservarlo entero, 0 que el numero de dentro no decia nada. Sobre "
            "ruido puro sale 0, que es lo que la hace legible.</dd>"
            "<dt>Pierde</dt><dd>En que fraccion de las particiones lo elegido termino la "
            "mitad reservada en perdidas. El PBO habla de puesto, esto de dinero.</dd>"
            "<dt>vs. la mediana</dt><dd>Si elegir con la regla bate a quedarse con la "
            "combinacion del medio, en toda la distribucion o solo en promedio.</dd></dl>"
            "<p class='note'>Este estudio NO dice si la estrategia va a funcionar hacia "
            "delante: rompe la cronologia a proposito para juzgar el procedimiento de "
            "eleccion, no esta historia. Lo que mira hacia delante es el holdout y el "
            "walk forward matrix.</p></main>")
