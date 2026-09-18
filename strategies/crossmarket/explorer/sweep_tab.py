"""The window-sweep tab: a grid of every market, then one market's curve, distributions and blocks."""

import numpy as np

from strategies.crossmarket import charts, figures, metrics, panel, sweep, tables
from strategies.crossmarket.explorer import sweep_views

# Net profit first: it is the number the owner reads a strategy in, and the one the tab opens on.
METRICS = ("net", "mean_r", "ret_dd", "dd", "sharpe", "pf")
TRENDS_ES = {"timing": "plano/decreciente → timing", "regime": "creciente → régimen",
             "no_pass": "sin pass a ningún tamaño: no hay aprobado que descomponer",
             "unassessable": "no evaluable: menos de dos tamaños calculados"}
TRENDS_SHORT = {"timing": '<span class="ok">timing</span>',
                "regime": '<span class="no">régimen</span>',
                "no_pass": "sin pass", "unassessable": "no evaluable"}
INTRO = (
    '<div class="note">Los tres modelos de colocación libre recolocan el ritmo de operar sobre '
    'toda la ventana del backtest, y con eso destruyen a la vez tres cosas: el <b>régimen</b> '
    'en que cae cada operación, su <b>calendario</b> y sus <b>rachas</b>. Aquí se vuelven a '
    'sortear dentro de bloques de calendario cada vez más cortos: cada operación sólo puede '
    'caer dentro de su propio bloque. Encoger el bloque devuelve el régimen y nada más, así '
    'que la curva separa qué parte del p es acierto y qué parte es herencia de régimen.</div>'
    '<details><summary>Qué destruye cada nulo, y cómo se lee la curva</summary>'
    '<div class="scroll"><table><tr><th>nulo</th><th>régimen</th><th>calendario</th>'
    '<th>rachas</th></tr>'
    '<tr><td>libre, ventana completa</td><td>destruido</td><td>destruido</td>'
    '<td>destruido</td></tr>'
    '<tr><td>libre, ventana encogiendo</td><td>← se restaura</td><td>destruido</td>'
    '<td>destruido</td></tr>'
    '<tr><td>Calendar Shift (referencia)</td><td>conservado</td><td>conservado</td>'
    '<td>conservado</td></tr></table></div>'
    '<div class="note"><b>Cómo se lee.</b> Si p se mantiene bajo al encoger, el acierto '
    'sobrevive aunque se le quite la suerte de régimen: es timing. Si p sube, el aprobado a '
    'ventana completa era herencia de régimen. <b>La curva nunca converge a Calendar '
    'Shift</b>: incluso con bloques cortos estos modelos siguen destruyendo calendario y '
    'rachas, que Calendar Shift conserva. Es otro eje; la línea naranja es una referencia, no '
    'un destino.<br><b>Léela siempre con las operaciones al lado.</b> Con bloques cortos hay '
    'menos sitio donde recolocar, el nulo se ensancha y p pierde resolución. Un tamaño en el '
    'que demasiadas operaciones caen en bloques con pocas operaciones o casi sin hueco libre '
    'no se calcula: sale como ✕, nunca como un número.</div></details>')


def axes(record: dict, cfg: dict) -> dict:
    """The three selectors the tab needs, for the panel to draw its sub-tabs.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        markets — the feeds this strategy was analysed on; models — the swept models as
        {key, name}; metrics — what the dropdown offers, Net profit first; windows — the
        block sizes, for the cone's selector. Everything was computed by the run and is held
        in memory, so switching any of them recomputes nothing.
    """
    return {"markets": list(record["runs"]),
            "models": [{"key": m, "name": panel.NAMES[m]} for m in cfg["sweep"]["models"]],
            "metrics": [{"key": k, "label": metrics.LABELS[k]} for k in METRICS],
            "windows": [{"key": w, "name": sweep_views.window_name(w)}
                        for w in sweep.ordered(cfg["sweep"]["windows"])]}


def grid(record: dict, cfg: dict, model: str, metric: str, current: str) -> str:
    """Every market's whole sweep for one model and one statistic, one row each.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.
        model: Which free-placement model the p-values are for.
        metric: Which statistic they are the p of.
        current: The market the detail below is showing, marked in the grid.

    Returns:
        A table with one column per block size and the trend beside it, so the question this
        tab exists to answer — does p hold when the regime comes back — is read without
        scrolling. Every row is clickable: it opens that market underneath.
    """
    labels = sweep.ordered(cfg["sweep"]["windows"])
    alpha = cfg["diagnostics"]["alpha"]
    head = tables._row(["mercado"] + [sweep_views.window_name(w) for w in labels]
                       + ["tendencia"], "th")
    body = []
    for feed, runs in record["runs"].items():
        sw = runs["sweep"]
        point = {w["window"]: pt for w, pt in zip(sw["windows"], sw["points"][model])}
        cells = "".join(
            '<td class="n">' + (sweep_views.p_cell(sweep_views.at(point[w], metric), alpha)
                                if w in point else "—") + "</td>" for w in labels)
        body.append(f'<tr class="pick{" on" if feed == current else ""}" data-market="{feed}">'
                    f'<td><code>{feed}</code></td>{cells}'
                    f'<td class="n">{TRENDS_SHORT[sw["trend"][model][metric]]}</td></tr>')
    return (f'<div class="scroll"><table class="gridpick">{head}{"".join(body)}</table></div>'
            '<p class="lede">Pulsa un mercado para ver su curva, sus distribuciones y sus '
            'bloques.</p>')


def detail(record: dict, cfg: dict, feed: str, model: str, metric: str, window: str) -> str:
    """One market's sweep: the three models on one curve, then the selected model's numbers.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.
        feed: Which market.
        model: Which free-placement model the table, the histograms and the highlighted line
            are for.
        metric: Which statistic every p, σ and histogram on the page is for.
        window: Which block size the equity cone draws.

    Returns:
        The block the panel swaps in when any selector changes. Three models used to mean
        three charts and three tables per market; they share an axis and the same blocks, so
        they are one chart, and only the numbers below depend on which is selected.
    """
    s, alpha = cfg["sweep"], cfg["diagnostics"]["alpha"]
    draws = cfg["nulls"]["draws"]
    floor = 1.0 / (1 + draws)
    sw = record["runs"][feed]["sweep"]
    reference = (None if sw["reference"] is None
                 else {"name": panel.NAMES[s["reference"]], "p": sw["reference"][metric]})
    series = [{"key": m, "name": panel.NAMES[m], "colour": charts.SERIES[i % len(charts.SERIES)],
               "points": [{"name": sweep_views.window_name(w["window"]),
                           "p": (sweep_views.at(pt, metric) or {}).get("p_value"),
                           "detail": f'≈{np.median([b["bars"] for b in w["blocks"]]):,.0f} '
                                     f'velas H1'}
                          for w, pt in zip(sw["windows"], sw["points"][m])]}
              for i, m in enumerate(s["models"])]
    return (f'<h2><code>{feed}</code> <span class="tagline">{panel.NAMES[model]} · '
            f'{metrics.LABELS[metric]} · {TRENDS_ES[sw["trend"][model][metric]]}</span></h2>'
            + figures.p_curves(series, reference, alpha, floor,
                               f"p de «{metrics.LABELS[metric]}» según el tamaño de bloque "
                               f"— {feed}", model)
            + f"<h3>Potencia punto a punto · {panel.NAMES[model]}</h3>"
            + sweep_views.power_table(sw, model, metric, alpha)
            + f"<h3>Distribuciones del nulo · {metrics.LABELS[metric]}</h3>"
            + sweep_views.distributions(sw, model, metric, draws)
            + "<h3>Equity de las tiradas confinadas</h3>"
            + '<div class="subtabs sub2" id="swWnTabs"></div>'
            + sweep_views.equity_cone(sw, model, feed, window, draws)
            + "<h3>Bloques</h3>" + sweep_views.blocks_detail(sw))


def sweep_view(record: dict, cfg: dict, feed: str, model: str, metric: str,
               window: str) -> dict:
    """The two halves the panel redraws together, since both depend on model and statistic.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.
        feed: Which market the detail is for.
        model: Which free-placement model.
        metric: Which statistic.
        window: Which block size the equity cone draws.

    Returns:
        {"grid", "detail"}: the front-page matrix and the open market, as HTML.
    """
    return {"grid": grid(record, cfg, model, metric, feed),
            "detail": detail(record, cfg, feed, model, metric, window)}


def sweep_tab(record: dict, cfg: dict) -> str:
    """The window sweep on every market this strategy was analysed on.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's controls. The grid and the open market arrive from /api/sweep/view, so
        changing model, statistic, market or block size never leaves the page and never
        recomputes anything.
    """
    return (INTRO
            + '<div class="note">El desplegable de indicador es <b>exploración</b>. La métrica '
              'del veredicto sigue siendo <code>mean_r</code> bajo <code>block_shift</code>, '
              'que es la que reporta la pestaña Backtest y la única elegida antes de mirar los '
              'números.</div>'
            + '<div class="subtabs sub2" id="swMdTabs"></div>'
            + '<div class="tools"><label>Indicador</label><select id="swMetric"></select></div>'
            + '<h3>Resumen — p por mercado y tamaño de bloque</h3>'
            + '<div id="swGrid"></div>'
            + '<div class="subtabs" id="swMkTabs"></div>'
            + '<div id="swView"></div>')
