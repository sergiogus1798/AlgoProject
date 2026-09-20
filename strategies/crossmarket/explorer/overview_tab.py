"""The tab the panel opens on: what these backtests did, at equal risk, and what holds them up.

It absorbed three tabs that used to sit apart — the old Resumen, Significancia and Correlación
— because they answered one question between them and nobody reads a strategy's drawdown on
one page and its confidence interval on another."""

import pandas as pd

from strategies.crossmarket.render import overlays, overview, panel, svg, tables
from strategies.crossmarket.simulate import joint
from strategies.crossmarket.verdict import alerts


def palette(record: dict) -> dict[str, str]:
    """One colour per market for the whole page.

    Args:
        record: What work.RESULTS holds.

    Returns:
        {feed: colour}, base asset first. Fixed here and passed down, so a market is the same
        colour in the equity overlay, in the master table's dot and in every histogram.
    """
    return svg.palette(list(record["equity"]), record["base"]["feed"])


def equity_note(cfg: dict) -> str:
    """The line under the equity overlay saying what its axes are."""
    return ("cada mercado con su propia cuenta independiente de "
            f'{cfg["equity"]["starting"]:,.0f} $ · eje vertical en % de esa cuenta · '
            "eje horizontal en fechas reales: un mercado cuyo backtest empieza más tarde "
            "empieza más tarde en el gráfico")


def explained(cfg: dict) -> str:
    """One paragraph per statistic on this page, because none of them explains itself."""
    target = cfg["equity"]["risk_target_dd"]
    return f'''<h2>Qué es cada número de esta página</h2>
<p><b>Net profit</b> — la suma del P/L que SQX reportó, no una reconstrucción. Es el dinero que
habría hecho esa cuenta con los tamaños de posición reales del backtest.</p>
<p><b>Return on account</b> — ese beneficio sobre la cuenta inicial. Aditivo, no compuesto: el
tamaño de posición del backtest es fijo por operación, así que no hay reinversión que componer.</p>
<p><b>Max drawdown</b> — la mayor caída de pico a valle de la curva, en dólares y en por ciento del
pico. Es <i>un</i> momento de la muestra: dos estrategias con el mismo DD pueden haberlo sufrido una
en un día y otra en tres años.</p>
<p><b>Return/DD</b> — beneficio dividido por esa caída. No depende del tamaño de cuenta ni del
apalancamiento, así que es lo más parecido a una comparación limpia entre mercados que hay en esta
tabla. Por debajo de 2 la estrategia devuelve menos de lo que llegó a pedir prestado al ánimo.</p>
<p><b>Sharpe per trade</b> — media dividida por desviación típica, <b>por operación</b> y sin
anualizar. No es el Sharpe anual que se cita en cualquier ficha: no se puede comparar con un 1,5 de
un fondo. Está en esta unidad porque es la que necesita el MinTRL de abajo.</p>
<p><b>Profit factor</b> — ganancia bruta dividida por pérdida bruta. 1,0 es no ganar nada; por
debajo de 1,2 el resultado suele ser una o dos operaciones.</p>
<p><b>Longest losing run</b> — la racha más larga de operaciones perdedoras seguidas. No mide
calidad, mide lo que hay que aguantar sin apagar el sistema.</p>
<p><b>Retorno a riesgo igualado</b> — el tamaño de cada mercado se multiplica hasta que su peor
caída es exactamente el {target:.0%} de la cuenta, y su retorno se multiplica por ese mismo factor.
Responde a «¿cuál fue mejor?» sin que gane el que más arriesgó.</p>
<p><b>MinTRL</b> (Bailey / López de Prado) — cuántas operaciones harían falta para que este Sharpe
se distinga de cero al 5%, dados su sesgo y sus colas. Colas gordas o sesgo negativo encarecen mucho
la factura. <b>No dice que la estrategia sea mala</b>: dice si esta muestra puede sostener esa
afirmación.</p>
<p><b>CI 90%</b> — intervalo de confianza por bootstrap de bloques sobre las operaciones reales. De
bloques, y no operación a operación, porque las velas dentro de una operación están
autocorrelacionadas y remuestrear sueltas estrecharía el intervalo de mentira.</p>
<p><b>Las dos columnas de operaciones.</b> «Operaciones (SQX)» son todas las que la databank
reporta, y es sobre todas ellas que se calculan el beneficio, la caída, el PF y la curva de capital
de esta página — por eso cuadran con SQX. «Usables en los tests» son las que ocupan al menos una
vela del gráfico. Una operación que abre y cierra dentro de la misma vela no tiene intervalo: no se
puede desplazar (1a), no tiene ventana ciega de su misma duración contra la que medirse (1b) ni
velas ocupadas que contar (1c). Son reales y su dinero está en el beneficio; lo que no pueden es
entrar en una comparación que necesita duración.</p>
<p><b>Correlación</b> — de los retornos <i>semanales</i> de cada curva de capital, no de sus
métricas. Dos mercados a 0,8 no son dos confirmaciones independientes: son una apuesta mirada dos
veces, y eso cambia cuánto vale que los dos «pasen».</p>'''


def overview_tab(record: dict, cfg: dict) -> str:
    """Everything the real backtests did, before any simulation is involved.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML: the strategy's tiles, the master table, the equal-risk comparison, the
        overlaid equity curves, the correlation matrix, the per-market test results, the
        mechanical checks and the explanations. No verdict: which strategy to keep is decided
        outside this study.
    """
    rows, base = pd.DataFrame(record["rows"]), record["base"]
    colours = palette(record)
    absent = ('<div class="note"><b>Sin operaciones en '
              + ", ".join(f"<code>{f}</code>" for f in record["missing"])
              + ".</b> Esta estrategia no llegó a disparar ni una vez ahí, así que ese mercado "
                "no tiene fila. Es un resultado sobre la estrategia, no un dato que falte."
                "</div>" if record["missing"] else "")
    return "".join([
        overview.breadth_block(record["summary"]), absent,
        "<h2>El backtest de cada mercado</h2>", overview.master(rows, base, colours),
        "<h3>A riesgo igualado</h3>",
        overview.equal_risk(rows, base, cfg["equity"]["risk_target_dd"]),
        "<h2>Las curvas de capital</h2>",
        overlays.equity(record["equity"], colours, base["feed"],
                        "Equity de cada mercado, en su propia cuenta", equity_note(cfg)),
        tables.correlation_section(record["correlation"]),
        "<h2>¿Se traslada? El nulo conjunto</h2>",
        joint.block(record["joint"], cfg["diagnostics"]["alpha"]),
        "<h2>Qué dijo cada test</h2>", overview.tests(rows, cfg["diagnostics"]["alpha"]),
        '<div class="note">Cada test tiene su propia pestaña, con su explicación y sus '
        'gráficos. Aquí sólo está el resultado.</div>',
        "<h2>Qué sostiene esos números</h2>", overview.evidence(rows, base),
        "<h2>Por dónde salieron las operaciones</h2>", tables.exits_table(rows),
        "<h2>Avisos</h2>", alerts.block(rows),
        "<h2>Comprobaciones mecánicas</h2>", panel.diagnostics(rows),
        explained(cfg)])
