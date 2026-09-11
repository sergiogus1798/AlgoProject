"""Assemble the study's HTML report: the figures, the tables, and what every number means."""

from pathlib import Path

import pandas as pd

from strategies.crossmarket import charts, inference

TEMPLATE = Path(__file__).with_name("panel.html")
SHOWN = 12          # strategies whose own distribution is drawn; the rest live in the CSV
# The report is read in Spanish; trade_models.RANDOMISES is code and stays in English.
RANDOMISES = {"block_shift": "sólo cuándo entra, dentro de su semestre y en su día y hora",
              "segment_permute": "cuándo entra, el orden de las operaciones y las rachas",
              "resampled_holds": "cuándo entra, qué duraciones y esperas ocurren, y el tiempo "
                                 "total en mercado",
              "fitted_holds": "cuándo entra, y las duraciones, sacadas de una distribución "
                              "ajustada a las reales"}
DIAGNOSTICS = [("convention", "convención de fill", "la que reprodujo los precios de SQX"),
               ("fill_error", "error de fill", "debe ser 0"),
               ("on_bar_open", "entradas en apertura de barra", "por debajo de 0,95 no vota"),
               ("calendar_kept", "calendario conservado", "debe ser 1,00"),
               ("atr_ratio", "volatilidad en las entradas", "1,00 = la media del mercado"),
               ("bar_cap", "salidas por tope de barras", "el resto salen por señal"),
               ("hold_median", "duración mediana (barras)", ""),
               ("point_value", "valor del punto medido", "de los propios trades, no supuesto"),
               ("cost_rate", "coste por operación", "fracción del precio")]


def _row(cells: list[str], tag: str = "td") -> str:
    """One table row, numbers right-aligned.

    Args:
        cells: Already-formatted cell contents.
        tag: "td" or "th".

    Returns:
        A table row. The first cell is a label and the rest are numbers.
    """
    first, rest = cells[0], cells[1:]
    return (f"<tr><{tag}>{first}</{tag}>"
            + "".join(f'<{tag} class="n">{c}</{tag}>' for c in rest) + "</tr>")


def headline(rows: pd.DataFrame, calls: pd.DataFrame, luck: dict) -> str:
    """The four numbers that decide whether the rest is worth reading.

    Args:
        rows: Every (strategy, market) row.
        calls: One row per strategy.
        luck: Expected false passes.

    Returns:
        A block of stat tiles. No plot: four unrelated scalars are a worse chart than they are
        a list.
    """
    kept = int((calls.verdict == inference.VERDICTS[0]).sum())
    beat = int((rows.testable & (rows.p <= inference.ALPHA)).sum())
    return (f'<div class="headline">'
            f'<div class="stat"><b>{len(calls)}</b><span>estrategias</span></div>'
            f'<div class="stat"><b>{rows.market.nunique()}</b><span>mercados adicionales</span></div>'
            f'<div class="stat"><b>{beat} / {int(rows.testable.sum())}</b>'
            f'<span>pares que baten al azar, de los evaluables</span></div>'
            f'<div class="stat"><b>{kept}</b><span>MANTENER, frente a '
            f'{luck["correlated"]:.1f} esperadas por suerte</span></div></div>')


def luck_note(calls: pd.DataFrame, luck: dict) -> str:
    """How much of the verdict is chance, said before any figure is shown.

    Args:
        calls: One row per strategy.
        luck: What inference.false_passes() returned.

    Returns:
        The framing paragraph. It comes first because a page of histograms invites the reader
        to believe the histograms, and this is the number that says how many of them to.
    """
    judged = int(calls.markets.median())
    if judged < inference.MIN_MARKETS:
        return (f'<div class="note"><b>La votación no se pudo celebrar.</b> La regla necesita '
                f'{inference.MIN_MARKETS} mercados con resultado utilizable y este estudio tuvo '
                f'{judged}, así que toda estrategia sale NO EVALUABLE por mucho que su p-valor '
                f'lo diga. Los p-valores de abajo son reales; el veredicto es que no hay '
                f'veredicto.</div>')
    return (f'<div class="note"><b>Cuántas pasarían por suerte.</b> Con {len(calls)} estrategias '
            f'votadas sobre {judged} mercados, la regla deja pasar <b>{luck["independent"]:.2f}</b> '
            f'por azar si los mercados fueran independientes, y <b>{luck["correlated"]:.1f}</b> si '
            f'sus resultados se parecen entre sí — que es la cifra que hay que usar. Compárala con '
            f'el número de MANTENER antes de llamar descubrimiento a nada.</div>')


def market_table(rows: pd.DataFrame) -> str:
    """The result per market, and whether it counted.

    Args:
        rows: Every (strategy, market) row.

    Returns:
        A scrollable table. The `vota` column is the one to read first: a market that does not
        vote contributes nothing, however good its p-value looks.
    """
    head = _row(["mercado", "operaciones", "real", "null", "ventaja", "p", "vota"], "th")
    body = []
    for market, g in rows.groupby("market", sort=False):
        vote = ('<span class="ok">sí</span>' if g.testable.all()
                else '<span class="no">no</span>')
        body.append(_row([f"<code>{market}</code>", f"{g.trades.median():.0f}",
                          f"{g.real_r.median():+.3f}", f"{g.null_r.median():+.3f}",
                          f"{g.edge_r.median():+.3f}", f"{g.p.median():.4f}", vote]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def diagnostics(rows: pd.DataFrame) -> str:
    """Every check that decides whether a market's result may be believed.

    Args:
        rows: Every (strategy, market) row.

    Returns:
        A table, one row per check and one column per market, with what each value should be.
    """
    markets = list(rows.market.unique())
    head = _row(["comprobación", *markets, "qué se espera"], "th")
    body = []
    for key, label, expect in DIAGNOSTICS:
        values = []
        for m in markets:
            v = rows.loc[rows.market == m, key].iloc[0]
            values.append(v if isinstance(v, str) else f"{v:,.4g}")
        body.append(_row([label, *values, expect]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def per_strategy(rows: pd.DataFrame, shapes: dict, models: list[str]) -> str:
    """One section per strategy and market: its distribution, and the four models beside it.

    Args:
        rows: Every (strategy, market) row.
        shapes: {"<strategy>|<market>": what inference.shape() returned}.
        models: The models that were run, the verdict's first.

    Returns:
        The figures. Capped at SHOWN strategies, best first, because a databank of hundreds
        cannot be read as hundreds of histograms — the CSV carries them all.
    """
    order = rows.groupby("strategy").p.min().sort_values().index[:SHOWN]
    out = []
    for name in order:
        out.append(f"<h3>{name}</h3>")
        for _, r in rows[rows.strategy == name].iterrows():
            key = f"{r.strategy}|{r.market}"
            verdict = ("bate al azar" if r.p <= inference.ALPHA else "no bate al azar")
            out.append(charts.distribution(
                shapes[key], r.market,
                f"{verdict} — p = {r.p:.4f}, ventaja {r.edge_r:+.3f}"))
            bars = [{"model": m, "p": r["p" if i == 0 else f"p_{m}"]}
                    for i, m in enumerate(models)]
            out.append(charts.models(bars, inference.ALPHA))
    return "".join(out)


def glossary(models: list[str]) -> str:
    """What every number on the page means, in the owner's own terms.

    Args:
        models: The models that were run.

    Returns:
        The closing section. The report is read by whoever the owner shows it to, and none of
        these quantities explains itself.
    """
    items = "".join(f"<li><code>{m}</code> — aleatoriza {RANDOMISES[m]}.</li>" for m in models)
    return f'''<h2>Qué significa cada número</h2>
<p><b>El estadístico.</b> Retorno logarítmico medio por operación, ya descontado el coste, dividido
por una constante de cada mercado (su ATR mediano). Esa constante es idéntica para el backtest real
y para los 5.000 aleatorios, así que no puede mover ningún p-valor: sólo sirve para que oro, plata y
petróleo se puedan comparar en el mismo eje.</p>
<p><b>El p-valor.</b> Qué fracción de los backtests aleatorios igualó o superó al real. 0,03 quiere
decir que 3 de cada 100 versiones al azar lo habrían hecho igual de bien. <b>No</b> es la
probabilidad de que la estrategia funcione.</p>
<p><b>La ventaja.</b> Real menos la mediana de los aleatorios, en las mismas unidades. Es el tamaño
del efecto, y es lo que hay que mirar cuando el p-valor sale ajustado.</p>
<p><b>Los modelos.</b> No hay una única forma correcta de convertir un backtest en uno aleatorio, y
la respuesta cambia con la elección. Por eso se corren varios: el primero decide, porque es el único
que cambia exactamente una cosa.</p>
<ul>{items}</ul>
<div class="note"><b>Lo que este informe no dice.</b> No detecta sobreajuste al activo base: mide si
el acierto se traslada a mercados que la estrategia nunca vio. Y no valida la curva de capital — el
estadístico está construido a propósito sin tamaño de posición, para que la comparación sea justa.
</div>'''


def render(title: str, sections: list[str]) -> str:
    """Put the assembled sections inside the page shell.

    Args:
        title: Browser title and page heading.
        sections: HTML blocks, in reading order.

    Returns:
        A self-contained page: no scripts, no fonts, no network. It has to open from a USB
        stick in five years.
    """
    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", title).replace("__BODY__", "\n".join(sections)))
