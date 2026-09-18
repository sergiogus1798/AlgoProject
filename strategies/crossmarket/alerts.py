"""Every reason to distrust a market's numbers, in the four parts a reader needs.

inference.py decides **whether** a warning fires; this says what it means. A warning used to
be one sentence, which left the owner unable to tell whether it invalidated the whole row or
one model: each now names what fired it, what it affects, what it does **not** affect, and
what to do about it."""

import pandas as pd

# key -> (what it is, what it affects, what it does not affect, what to do). The `affects`
# half is the part that was missing: `bad_hold_fit` touches exactly one null model, and
# `no_drift` touches exactly one number, while the earlier wording implied the whole market.
TEXTS = {
    "few_trades": (
        "Hay menos operaciones en este mercado que el mínimo de lectura "
        "(<code>diagnostics.min_trades</code>).",
        "A todo lo que lleve un intervalo de confianza o un p-valor: con pocas operaciones "
        "los intervalos son anchos y los p-valores, inestables.",
        "El mercado no se descarta, y sus números no están mal calculados: están poco "
        "determinados.",
        "Léelo como una indicación, no como un resultado. Mira el tamaño del efecto "
        "(ventaja, A, alfa de 1b) antes que cualquier p."),
    "pending_fills": (
        "Parte de las entradas no cae en la apertura de una vela: son órdenes pendientes "
        "(limit o stop) ejecutadas <b>dentro</b> de la vela.",
        "Al test 1a. Un modelo nulo sólo sabe colocar una operación «en la vela t» y la "
        "valora a su apertura, así que para esa fracción de operaciones no reproduce lo que "
        "el backtest hizo: es una selección condicionada al precio.",
        "A 1b y 1c no les afecta: ninguno de los dos usa modelos nulos. Tampoco invalida el "
        "backtest — esas operaciones ocurrieron de verdad.",
        "Lee el p de 1a de este mercado como aproximado, y tanto más cuanto menor sea el "
        "porcentaje de la izquierda."),
    "fill_mismatch": (
        "Ninguna convención de fill reproduce los precios que SQX registró: el error mediano "
        "no es cero.",
        "A todo lo que compare el backtest real con algo simulado, que es 1a y el estrés de "
        "coste. Si el real y el nulo se valoran distinto, el p mide la diferencia entre dos "
        "valoradores y no el acierto de la estrategia.",
        "Nada más de la página: 1b y 1c usan la misma serie de precios en los dos lados de "
        "su propia resta.",
        "Éste sí es grave. Comprueba que las velas del export son las del mismo feed y "
        "timeframe con que se corrió el retest."),
    "no_drift": (
        "La deriva propia de este mercado no se distingue de cero "
        "(<code>exposure.mu_min_t</code>), o es negativa.",
        "Sólo a <b>E</b>, que divide por esa deriva. Un denominador estadísticamente nulo da "
        "cocientes enormes o de signo invertido: medido, Brent con t = −0,11 daba E = −69,4.",
        "<b>A no se ve afectada</b> — resta en vez de dividir — ni tampoco A por unidad de "
        "riesgo, que divide por la volatilidad típica y ésa nunca es cero. De hecho Brent "
        "era el mercado con la A más alta de los tres.",
        "Ignora E aquí, o léela con su intervalo de Fieller al lado, que en este caso será "
        "no acotado. El número que vale en este mercado es A por unidad de riesgo."),
    "calendar_lost": (
        "Las entradas simuladas no caen en el mismo día de la semana y la misma hora que las "
        "reales.",
        "Al modelo nulo que lo perdió. Una operación de ocho velas abierta un viernes por la "
        "tarde cruza el fin de semana y una abierta un martes no, así que si el calendario "
        "no se conserva, el nulo y el real no viven el mismo mercado.",
        "A los modelos de colocación libre no les aplica: por construcción destruyen el "
        "calendario y se leen sabiéndolo.",
        "Debe valer 1,00 en Calendar Shift. Si no lo vale, no leas su p como atribuible al "
        "momento de entrada."),
    "short_sample": (
        "Dado este Sharpe, este sesgo y estas colas, harían falta más operaciones de las que "
        "hay para que el Sharpe se distinga de cero (Bailey / López de Prado).",
        "A cualquier afirmación sobre el Sharpe de este mercado.",
        "<b>No dice que la estrategia sea mala.</b> Dice que esta muestra no puede sostener "
        "esa afirmación concreta. El resto de los tests tienen sus propios tamaños de efecto "
        "y sus propios intervalos.",
        "Si quieres afirmar algo sobre el Sharpe aquí, necesitas más muestra. Mientras "
        "tanto, apóyate en 1b, que no pasa por el Sharpe."),
    "bad_hold_fit": (
        "La distribución ajustada a las duraciones reales no las describe (KS por debajo de "
        "alpha).",
        "Sólo al modelo <b>Fitted Distributions Sequence</b>, que sortea duraciones nuevas de "
        "esa distribución. Si el ajuste no pega, ese modelo es una afirmación sobre la "
        "distribución equivocada.",
        "Los otros tres modelos reutilizan las duraciones reales y son inmunes a esto.",
        "Lee el p de ese modelo con desconfianza y quédate con los otros tres. Es también el "
        "síntoma de una flota con dos poblaciones de duración — tope de velas y salida por "
        "señal — que ninguna distribución de una moda describe."),
    "off_grid": (
        "Parte de las operaciones reales <b>no ocupa ninguna vela</b>: abren y cierran dentro "
        "de la misma, casi siempre salidas <code>Exit Signal</code> de duración <code>0s</code>.",
        "A los tres tests que necesitan una duración: 1a no puede desplazar una operación sin "
        "intervalo, 1b no tiene ventana ciega de su misma duración contra la que medirla, y 1c "
        "no tiene velas ocupadas que contar. Esas operaciones quedan fuera de los tres.",
        "<b>A los números del backtest no les afecta</b>: el beneficio, la caída, el PF y la "
        "curva de capital de la pestaña Backtest se calculan sobre <b>todas</b> las "
        "operaciones que reporta SQX, así que cuadran con la databank. Por eso la tabla "
        "maestra enseña las dos cuentas.",
        "Lee los p-valores sabiendo que describen la fracción usable de la estrategia. Medido "
        "sobre este databank: 1,84% de 92.329 operaciones, hasta un 9,8% en el peor par."),
}
# What number fired each warning, so the reader sees the trigger and not only the rule.
TRIGGER = {
    "few_trades": lambda r: f'{int(r["trades"])} operaciones',
    "pending_fills": lambda r: f'{r["on_bar_open"]:.1%} de entradas en apertura de vela',
    "fill_mismatch": lambda r: f'error de fill {r["fill_error"]:.4g}',
    "no_drift": lambda r: f'deriva del mercado t = {r["mu_t"]:+.2f}',
    "calendar_lost": lambda r: f'calendario conservado {r["calendar_kept"]:.2f}',
    "short_sample": lambda r: (f'{int(r["trades"])} operaciones frente a '
                               f'{r["min_track_needed"]:,.0f} necesarias'),
    "bad_hold_fit": lambda r: f'KS del ajuste p = {r["hold_ks_p"]:.4f}',
    "off_grid": lambda r: (f'{int(r["dropped"])} de {int(r["trades_all"])} operaciones '
                           f'({r["dropped"] / r["trades_all"]:.1%}), '
                           f'{r["dropped_pnl"]:+,.0f} $'),
}


def one(key: str, row: dict) -> str:
    """One warning as a block: the trigger, then what it does and does not touch.

    Args:
        key: A key of inference.WARNINGS.
        row: The (strategy, market) row that fired it.

    Returns:
        An HTML block.
    """
    what, affects, spares, todo = TEXTS[key]
    return (f'<div class="alert"><p class="alert-head"><b>{what}</b> '
            f'<span class="trigger">{TRIGGER[key](row)}</span></p>'
            f'<p><b>Afecta a:</b> {affects}</p>'
            f'<p><b>No afecta a:</b> {spares}</p>'
            f'<p><b>Qué hacer:</b> {todo}</p></div>')


def block(rows: pd.DataFrame) -> str:
    """Every market's warnings, spelled out.

    Args:
        rows: Per-market rows carrying a `warnings` list.

    Returns:
        One section per market, or a line saying it collected none. No market is ever hidden
        by these: they are the context its numbers are read in.
    """
    out = []
    for r in rows.itertuples():
        out.append(f'<h3><code>{r.feed}</code></h3>')
        row = r._asdict()
        out.append("".join(one(w, row) for w in r.warnings) if r.warnings
                   else '<p><span class="ok">Sin avisos.</span> Ninguna de las ocho '
                        'comprobaciones saltó en este mercado.</p>')
    return "".join(out)
