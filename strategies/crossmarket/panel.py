"""The shared tables and the Spanish wording the panel's tabs are built from."""

import pandas as pd

# What each model is called on screen. The registry keys stay as they are — they are the
# contract trade_models.MODELS, config.yaml and every docstring share — and this is the only
# place a reader's name for one lives.
NAMES = {"segment_permute": "Shuffled Sequence", "resampled_holds": "Resampled Sequence",
         "fitted_holds": "Fitted Distributions Sequence", "block_shift": "Calendar Shift"}

# One paragraph per model, written as a ladder: each says what it adds over the one before it,
# because that difference is the only reason to run more than one. The first three are the same
# family — the rhythm re-laid anywhere in the sample — and Calendar Shift is the one that is not.
EXPLAINED = {
    "segment_permute": (
        "<b>El punto de partida.</b> Coge la secuencia real de duraciones y esperas, "
        "<b>baraja su orden</b>, y la extiende desde una vela al azar de toda la muestra. "
        "Las duraciones y los huecos siguen siendo <i>exactamente los mismos</i> en conjunto "
        "— ni uno más ni uno menos — así que el tiempo total en mercado es idéntico al real. "
        "Lo que se destruye es el orden, las rachas y el calendario.<br><br>"
        "Contesta: <i>¿este mismo ritmo de operar, colocado en cualquier punto de la "
        "ventana del backtest, habría ganado lo mismo?</i> Una tirada puede caer en un tramo "
        "bueno y heredar su régimen, y por eso suele ser algo más difícil de batir que "
        "Calendar Shift — aunque no siempre. <b>La ventana es la del backtest</b>, no la del "
        "fichero de velas: si el backtest va de 2008 a 2022, ninguna simulación opera en "
        "2007 ni en 2023."),
    "resampled_holds": (
        "<b>Lo que añade sobre Shuffled Sequence:</b> ya no conserva el conjunto. En vez de "
        "barajar las duraciones reales, las <b>sortea con reemplazo</b> — una duración puede "
        "salir dos veces y otra ninguna. Consecuencia: el <b>tiempo total en mercado varía "
        "de tirada en tirada</b>, cosa que Shuffled Sequence fija.<br><br>"
        "Contesta: <i>¿el ritmo de operar de esta estrategia, como población y no como esta "
        "realización concreta, vale algo?</i> En la práctica sobre estos datos da casi "
        "exactamente lo mismo que Shuffled Sequence (σ dentro del 2%, p dentro de 0,005): "
        "una vez que la colocación es libre, dominar dónde cae la tirada importa mucho más "
        "que si el multiset se conserva."),
    "fitted_holds": (
        "<b>Lo que añade sobre Resampled Sequence:</b> las duraciones ya <b>ni siquiera "
        "salen de las reales</b>. Se ajusta una distribución a ellas — binomial negativa si "
        "están sobredispersas, Poisson si no — y se sortean duraciones nuevas de esa "
        "distribución.<br><br>"
        "Contesta: <i>¿un sistema con esta</i> forma <i>de duraciones, entrando al azar, "
        "habría ido igual?</i> Es el único de los tres primeros que se separa de verdad de "
        "los otros dos, porque cambia el objeto medido y no solo su colocación. "
        "<b>Cuidado con esta flota</b>: sus duraciones son casi constantes, ninguna "
        "distribución las describe, y el panel imprime la dispersión y el KS al lado — si el "
        "ajuste no pega, este modelo es una afirmación sobre la distribución equivocada."),
    "block_shift": (
        "<b>Este no pertenece a la familia de los tres anteriores, y esa es toda la razón "
        "de que exista.</b> Los tres de arriba levantan la tirada entera y la sueltan en "
        "cualquier punto de los 22 años: cambian a la vez <i>cuándo</i> entra, el <i>orden</i> "
        "de las operaciones, su <i>calendario</i> y el <i>régimen de mercado</i> en que "
        "viven. Si uno de ellos da un p bajo, no sabes a cuál de esas cuatro cosas "
        "atribuirlo.<br><br>"
        "Calendar Shift mueve <b>cada operación por separado</b>, un número entero de "
        "semanas, y solo <b>dentro de su propio semestre</b> y cayendo en <b>el mismo día de "
        "la semana y a la misma hora</b>. Conserva por tanto tres cosas que los otros "
        "destruyen: el régimen (una operación de 2011 se compara contra 2011, no contra "
        "2020), el calendario (los huecos de fin de semana, las sesiones y el cierre del "
        "viernes son idénticos) y las rachas (una agrupación de operaciones sigue agrupada). "
        "<b>Es el único que cambia exactamente una cosa</b> — cuándo entra — y por eso el "
        "único cuyo p bajo se puede atribuir al acierto en el momento de entrar y a nada "
        "más. Es la `p` que sale en el Resumen.<br><br>"
        "El precio de esa precisión: al restringir tanto la colocación suele salirle una "
        "distribución algo más estrecha y un p algo más bajo — medido sobre 8 pares "
        "estrategia×mercado, <b>el p más bajo en 7 de ellos</b>, y la distribución más "
        "estrecha en 5. No es sistemáticamente el más exigente, es el <b>atribuible</b>. Así "
        "que <b>una estrategia que aguanta los cuatro dice bastante más que una que solo "
        "aguanta este</b>."),
}

# Why there is no fifth model. Kept in the panel so the question is not reopened from scratch.
RETIRED = (
    "<b>Renewal Process, retirado el 15-09-2026.</b> Recorría las velas y, estando plano, "
    "decidía entrar con la frecuencia empírica, de modo que también el número de operaciones "
    "era aleatorio. Sobre el papel añadía algo; medido sobre 8 pares estrategia×mercado <b>no "
    "añadía nada</b>: misma anchura que Resampled Sequence dentro del 2% y mismo p dentro de "
    "0,004, en todos ellos. Una vez que la colocación es libre sobre toda la muestra, lo que "
    "manda es en qué década cae la tirada, y eso los tres primeros ya lo aleatorizan igual.")

# The report is read in Spanish; trade_models.RANDOMISES is code and stays in English.
RANDOMISES = {"segment_permute": "cuándo entra, el orden, las rachas y el régimen",
              "resampled_holds": "lo anterior, y además qué duraciones ocurren y el tiempo "
                                 "total en mercado",
              "fitted_holds": "lo anterior, y además las duraciones mismas, sacadas de una "
                              "distribución ajustada",
              "block_shift": "sólo cuándo entra, dentro de su semestre y en su día y hora"}
# The Spanish mirror of inference.WARNINGS, for the pages the owner reads.
WARNINGS_ES = {
    "few_trades": "muy pocas operaciones en este mercado para decir nada firme",
    "pending_fills": "parte de las entradas no cae en apertura de vela: son órdenes "
                     "pendientes que ningún modelo nulo reproduce",
    "fill_mismatch": "los precios no se reproducen desde las velas: el real y el nulo no "
                     "están valorados igual",
    "no_drift": "el mercado no tiene deriva distinguible de cero, así que E no significa nada",
    "calendar_lost": "el nulo no conserva el día y la hora de las entradas reales",
    "short_sample": "el Sharpe observado necesita más operaciones de las que hay para "
                    "distinguirse de cero",
    "bad_hold_fit": "la distribución ajustada a los holds no la describe",
}
DIAGNOSTICS = [("convention", "convención de fill", "la que reprodujo los precios de SQX"),
               ("fill_error", "error de fill", "debe ser 0"),
               ("on_bar_open", "entradas en apertura de barra", "1,00 = ninguna pendiente"),
               ("off_grid", "operaciones fuera de la rejilla de velas", "no se pueden valorar"),
               ("calendar_kept", "calendario conservado", "1,00 en block_shift"),
               ("friday_exit", "salidas por cierre de viernes", "el nulo las reproduce"),
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


def market_table(rows: pd.DataFrame) -> str:
    """The result per market, and whether it counted.

    Args:
        rows: Every (strategy, market) row.

    Returns:
        A scrollable table. No market is ever excluded; the `avisos` column says how many
        reasons there are to distrust its numbers, and the warnings tab spells each one out.
    """
    head = _row(["mercado", "categoría", "operaciones", "real", "null", "ventaja",
                "p (1a)", "p (1b pareado)", "avisos"], "th")
    body = []
    for market, g in rows.groupby("feed", sort=False):
        count = int(g.warnings.map(len).sum())
        flag = ('<span class="ok">ninguno</span>' if not count
                else f'<span class="no">{count}</span>')
        body.append(_row([f"<code>{market}</code>", g.category.iloc[0],
                          f"{g.trades.median():.0f}",
                          f"{g.real_r.median():+.3f}", f"{g.null_r.median():+.3f}",
                          f"{g.edge_r.median():+.3f}", f"{g.p.median():.4f}",
                          f"{g.paired_p.median():.4f}", flag]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def diagnostics(rows: pd.DataFrame) -> str:
    """Every check that decides whether a market's result may be believed.

    Args:
        rows: Every (strategy, market) row.

    Returns:
        A table, one row per check and one column per market, with what each value should be.
    """
    markets = list(rows.feed.unique())
    head = _row(["comprobación", *markets, "qué se espera"], "th")
    body = []
    for key, label, expect in DIAGNOSTICS:
        values = []
        for m in markets:
            v = rows.loc[rows.feed == m, key].iloc[0]
            values.append(v if isinstance(v, str) else f"{v:,.4g}")
        body.append(_row([label, *values, expect]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


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
<p><b>El test pareado (1b).</b> Compara cada operación real con la media exacta de <i>todas</i> las
ventanas de su misma duración dentro de su mismo semestre. El coste aparece en los dos lados y se
cancela, así que este test no depende de ninguna suposición de coste ni de ningún modelo nulo — y
tampoco dice si la estrategia gana dinero, sólo si sus entradas baten a entradas ciegas de la misma
duración.</p>
<p><b>E y A (test 1c).</b> A es el exceso por vela sobre la vela media del mercado: mide el acierto
con la deriva descontada. E es ese mismo cociente en vez de resta, y <b>sólo se muestra cuando la
deriva del mercado es distinguible de cero</b>: dividir por una deriva que estadísticamente es cero
da números como −69, que leen al revés de lo que son.</p>
<p><b>Los modelos.</b> No hay una única forma correcta de convertir un backtest en uno aleatorio, y
la respuesta cambia con la elección. Por eso se corren varios: el primero decide, porque es el único
que cambia exactamente una cosa.</p>
<ul>{items}</ul>
<div class="note"><b>Aquí no hay veredicto.</b> Ningún número de esta página decide si una
estrategia se queda o se descarta, y ningún mercado se oculta por haber fallado una comprobación:
cada uno sale con todos sus números y con la lista de motivos para desconfiar de ellos. La decisión
la toma el dueño fuera de este estudio.</div>
<div class="note"><b>Lo que este informe no dice.</b> No detecta sobreajuste al activo base: mide si
el acierto se traslada a mercados que la estrategia nunca vio. Y no valida la curva de capital — el
estadístico está construido a propósito sin tamaño de posición, para que la comparación sea justa.
</div>'''
