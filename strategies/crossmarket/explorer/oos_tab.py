"""The tab for the base asset's out-of-sample stretch: the same 1a, on the same market, alone."""

import pandas as pd

from strategies.crossmarket.explorer import simulations
from strategies.crossmarket.render import panel
from strategies.crossmarket.verdict import alerts


def lead(oos: dict, cfg: dict) -> str:
    """The question this tab answers and the one thing that must be read before its numbers.

    Args:
        oos: What oos_run.run() returned.
        cfg: The configuration that run was made with.

    Returns:
        The tab's opening block. The caveat is here and not only in Avisos because the
        headline number is a p-value on a stretch the project's own acceptance conditions
        read, and a reader who sees the p first will not go looking for the footnote.
    """
    span, row = oos["span"], oos["row"]
    return (f'<div class="lead"><h3>La pregunta</h3>'
            f'<p><i>Sobre el tramo del backtest principal que la estrategia no optimizó '
            f'—{span["from"]} a {span["to"]}—, ¿sus entradas eligieron momento mejor que el '
            f'azar?</i></p>'
            f'<p>Es exactamente el test de <b>Entrada aleatoria (1a)</b> de la pestaña de al '
            f'lado, con los mismos modelos nulos, las mismas '
            f'{cfg["nulls"]["draws"]:,} tiradas y las mismas posiciones y costes reales — '
            f'pero corrido sobre <code>{oos["feed"]}</code> recortado a ese tramo y nada '
            f'más. Las velas se recortan con él: un nulo que pudiera colocar una operación '
            f'en 2010 no estaría probando el OOS, estaría probando el backtest entero con '
            f'menos operaciones.</p>'
            f'<p><b>Qué se prueba.</b> {row["trades_all"]} de las {oos["of"]} operaciones '
            f'del backtest de oro viven enteras dentro del tramo; una que cruce cualquiera '
            f'de los dos bordes se descarta en vez de recortarse, porque recortarla '
            f'inventaría una salida que la estrategia nunca tomó.</p>'
            f'<p><b>Por qué no cuenta con plata y Brent.</b> No es otro mercado: es el mismo, '
            f'sobre fechas que solapan con las suyas. El nulo conjunto de la pestaña Backtest '
            f'está dimensionado para mercados distintos desplazados a la vez, así que esta '
            f'fila se reporta aparte y no entra en él, ni en el recuento de mercados, ni en '
            f'el portfolio, ni en la matriz de correlación.</p>'
            f'<p><b>Y lo que no es.</b> Este tramo <b>no es dato virgen</b> — las condiciones '
            f'de aceptación del proyecto lo leyeron. El aviso del final lo explica con la '
            f'medición detrás, y es lo primero que hay que leer.</p></div>')


def oos_tab(record: dict, cfg: dict) -> str:
    """The whole tab: one equity cone, one histogram and one metric table per null model.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML, or a line saying the base asset declares no out-of-sample range.
        Rendered whole rather than behind selectors: there is one market here and four
        models, which is four figures — the random-entry tab is interactive because it
        multiplies markets by models, and this does not.
    """
    oos = record.get("oos")
    if oos is None:
        return ('<div class="note">Este activo base no declara ningún tramo fuera de muestra '
                'en <code>assets/_markets.yaml</code> (<code>out_of_sample</code>), así que no hay '
                'nada que probar aquí. Se lee del <code>&lt;OutOfSample&gt;</code> del '
                'proyecto y se declara a mano: el export marca <code>Sample type = IST</code> '
                'en todas las operaciones y no sabe dónde está el corte.</div>')
    shown = oos["row"]["feed"]
    view = {"runs": {shown: oos["runs"]}}
    out = [lead(oos, cfg)]
    for model in cfg["nulls"]["models"]:
        out.append(f'<h3>{panel.NAMES[model]}</h3>')
        out.append(simulations.random_view(view, cfg, shown, model, "mean_r"))
    out.append("<h2>Qué hay que desconfiar de estos números</h2>")
    out.append(alerts.block(pd.DataFrame([oos["row"]])))
    return "".join(out)
