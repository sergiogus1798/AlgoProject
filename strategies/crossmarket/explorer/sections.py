"""The panel's per-strategy tabs, rendered by the same functions everywhere."""

import pandas as pd

from strategies.crossmarket.render import figures, overlays, panel, tables
from strategies.crossmarket.verdict import alerts
from strategies.crossmarket.explorer import (overview_tab, portfolio_tab, simulations,
                                             stress_tab as stress_view, sweep_tab)


def _rows(record: dict) -> pd.DataFrame:
    """The strategy's per-market rows as a frame, for every renderer here.

    Args:
        record: What work.RESULTS holds for one strategy.

    Returns:
        One row per market analysed, base asset excluded.
    """
    return pd.DataFrame(record["rows"])


def warnings_tab(record: dict, cfg: dict) -> str:
    """Every reason to distrust each market's numbers.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML.
    """
    return ('<div class="note">Ningún mercado se excluye por esto. Un aviso es contexto para '
            'leer el número, no una razón para esconderlo — y cada uno dice <b>a qué afecta y '
            'a qué no</b>, porque casi ninguno invalida la fila entera.</div>'
            + alerts.block(_rows(record)))


def paired_tab(record: dict, cfg: dict) -> str:
    """Test 1b across the strategy's markets.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML, with the base asset's own paired result shown as the reference.
    """
    base, rows = record["base"], _rows(record)
    note = (f'<div class="note">Referencia — en el activo base <code>{base["feed"]}</code>, '
            f'donde la estrategia fue optimizada, el test pareado da p = {base["paired_p"]:.4f} '
            f'con {base["paired_beat"]:.1%} de operaciones ganando a su ventana media. Eso dice '
            f'que el código mide lo que dice medir, y nada sobre la estrategia.</div>')
    return ('<div class="lead"><h3>La pregunta</h3>'
            '<p><i>Dado que esta estrategia iba a estar N velas dentro del mercado en aquel '
            'momento, ¿eligió N velas mejores que las N velas medias de ese mismo tramo?</i>'
            '</p><p>Cada operación real se compara contra la media <b>exacta</b> —no '
            'muestreada— de <b>todas</b> las ventanas de su misma duración dentro de su '
            'ventana de referencia. La diferencia es el <b>alfa de timing</b>. El coste '
            'aparece en los dos lados y se cancela, así que este test <b>no dice si la '
            'estrategia gana dinero</b>: dice si sus entradas eligen momento. Es el único '
            'test del estudio que no necesita ni modelo nulo ni suposición de coste, y el '
            'único cuya referencia es exacta en vez de simulada.</p>'
            '<p><b>Cómo se lee.</b> Alfa positivo con p baja: el momento de entrar aporta. '
            'Alfa ≈ 0 con la estrategia ganando: gana por <i>estar dentro</i> del mercado, no '
            'por elegir cuándo. Alfa negativo: sus entradas son peores que entrar al azar en '
            'ese mismo tramo.</p></div>'
            + figures.bars_by_market(
                [{"market": r["feed"], "alfa (bps)": r["paired_bps"]} for r in record["rows"]],
                "alfa (bps)", "Alfa de timing por operación, en puntos básicos", rule=0.0)
            + tables.paired_table(rows)
            + "<h3>¿Depende de cómo se define «el mismo tramo»?</h3>"
            + '<p class="lede">La ventana centrada le da a cada operación su propio entorno, '
              'simétrico, sin fronteras. La partición en semestres es la que usa Calendar '
              'Shift, y tiene un defecto conocido: una operación que entra tres días antes de '
              'que acabe el semestre se mide contra un tramo que ya casi ha pasado, y dos '
              'operaciones separadas por una semana a caballo de la frontera reciben '
              'referencias disjuntas.</p>'
            + tables.sensitivity_table(rows) + note)


def exposure_tab(record: dict, cfg: dict) -> str:
    """Test 1c across the strategy's markets.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML. A per unit of risk is charted rather than E, which exists only where
        the market's own drift does.
    """
    return ('<div class="lead"><h3>La pregunta</h3>'
            '<p><i>¿Las velas que esta estrategia ocupó fueron mejores que la vela media de '
            'este mercado, y cuánta de la deriva total del mercado capturó por unidad de '
            'exposición?</i></p>'
            '<p><b>Diferencia con 1b.</b> 1b mide por <b>operación</b> y descuenta el régimen '
            '—compara contra el mismo tramo—. 1c mide por <b>vela</b> y <b>no</b> descuenta '
            'el régimen: compara contra toda la muestra. Una estrategia que acierta el '
            '<i>año</i> pero entra al azar dentro de él saca A alta y 1b sin p. Una que '
            'acierta el <i>momento</i> en tramos flojos saca lo contrario. Que discrepen es '
            'informativo, no un error.</p>'
            '<p><b>A</b> resta la vela media del mercado; <b>E</b> divide por ella. Por eso A '
            'está definida siempre y E no: donde la deriva del mercado no se distingue de '
            'cero, su intervalo de Fieller sale <b>no acotado</b>, y la columna de la derecha '
            'dice en qué fracción de las réplicas el denominador cambiaba de signo.</p></div>'
            + figures.bars_by_market(
                [{"market": r["feed"], "A / unidad": r["risk_normalised"]}
                 for r in record["rows"]],
                "A / unidad", "Exceso por vela sobre la vela media, por unidad de riesgo",
                rule=0.0)
            + tables.exposure_table(_rows(record)))


def fingerprint_tab(record: dict, cfg: dict) -> str:
    """Behavioural fingerprint against the base asset, with its distributions drawn.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML: what every metric means, the table, and four overlaid histograms per
        market against the base asset.
    """
    rows, base = _rows(record), record["base"]["feed"]
    colours = overview_tab.palette(record)
    out = ['<div class="lead"><h3>La pregunta</h3>'
           f'<p><i>¿Esta estrategia hace en este mercado lo mismo que hace en '
           f'<code>{base}</code>, o hace otra cosa que también gana?</i></p>'
           '<p>Todo lo de esta pestaña es <b>descriptivo</b>: se compara contra el activo '
           'base, nunca contra el azar. Un edge que se traslada debería <i>comportarse</i> '
           'parecido; si aquí dura el triple y sufre la mitad, no es el mismo edge dos veces, '
           'son dos cosas distintas y la segunda no está validada por la primera.</p>'
           '<h3>Qué mide cada número</h3><ul class="defs">'
           '<li><b>KS de duraciones</b> — test de Kolmogórov-Smirnov entre la distribución de '
           'duraciones aquí y la del oro. <b>p baja = distribuciones distintas</b>, que es lo '
           'contrario de lo habitual en esta página: aquí una p baja es un aviso.</li>'
           '<li><b>MAE (×ATR)</b> — cuánto llegó a ir en contra cada operación antes de '
           'cerrarse, en múltiplos del ATR de su vela de entrada. Normalizado así porque la '
           'plata se mueve el triple que el oro y sin normalizar no se comparan.</li>'
           '<li><b>MFE (×ATR)</b> — lo mismo, a favor: cuánto llegó a valer la operación en '
           'su mejor momento.</li>'
           '<li><b>Captura de MFE</b> — qué fracción de esa excursión favorable acabó '
           'convirtiendo en beneficio realizado. Mide la <b>salida</b>, no la entrada — por '
           'eso vive aquí y no en 1c. 0,3 significa que la estrategia se queda con menos de '
           'un tercio de lo que llegó a tener.</li>'
           '<li><b>Skew</b> — asimetría de los retornos por operación. Negativo = muchas '
           'ganancias pequeñas y pocas pérdidas grandes, el perfil que revienta cuentas.</li>'
           '<li><b>Kurtosis</b> — peso de las colas. Alto = el resultado depende de pocas '
           'operaciones, y quitarlas lo cambia todo.</li>'
           '<li><b>Tail ratio</b> — |p95| / |p5|. Por debajo de 1 la peor cola pesa más que '
           'la mejor.</li></ul></div>',
           tables.fingerprint_table(rows)]
    for r in record["rows"]:
        out.append(f'<h3><code>{r["feed"]}</code> frente a <code>{base}</code></h3>')
        out.append('<div class="pair wrap">' + "".join(
            overlays.distributions(h, r["feed"], base, colours[r["feed"]], colours[base])
            for h in r["fingerprint"]["hists"]) + "</div>")
    return "".join(out)


def glossary_tab(record: dict, cfg: dict) -> str:
    """What every number on the page means, in the owner's own terms.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The closing section; none of these quantities explains itself.
    """
    return panel.glossary(cfg["nulls"]["models"])


TABS = [("overview", "Backtest"), ("random", "Entrada aleatoria (1a)"),
        ("models", "Modelos"), ("sweep", "Barrido de ventana"), ("paired", "Pareado (1b)"),
        ("exposure", "Exposición (1c)"), ("stress", "Coste y ejecución"),
        ("fingerprint", "Huella"), ("portfolio", "Portfolio"), ("warnings", "Avisos"),
        ("glossary", "Glosario")]
RENDER = {"overview": overview_tab.overview_tab, "random": simulations.random_tab,
          "models": simulations.models_tab, "sweep": sweep_tab.sweep_tab,
          "stress": stress_view.stress_tab, "paired": paired_tab, "exposure": exposure_tab,
          "fingerprint": fingerprint_tab, "portfolio": portfolio_tab.portfolio_tab,
          "warnings": warnings_tab, "glossary": glossary_tab}


def section(name: str, record: dict, cfg: dict) -> str:
    """One tab's HTML, for the strategy the panel is showing.

    Args:
        name: A key of RENDER.
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's content.
    """
    return RENDER[name](record, cfg)
