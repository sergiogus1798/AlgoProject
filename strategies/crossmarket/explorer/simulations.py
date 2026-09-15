"""The three tabs that draw simulated distributions and equity cones: 1a, the models, the
execution stress. Split from sections.py so both stay under CODESTYLE's 250-line cap."""

import pandas as pd

from strategies.crossmarket import charts, figures, metrics, panel, tables


def _chip(text: str, passes: bool) -> str:
    """One cell of the p / Bate a columns, coloured by whether it clears the 95% criterion.

    Args:
        text: The number, already formatted.
        passes: Whether it clears.

    Returns:
        A highlighted span. Deliberately not the figures' own blue and orange, which mean
        "simulated" and "real" everywhere else on the page — a third pair of colours here
        keeps "passes / does not" from being read as "null / observed".
    """
    return f'<span class="chip-{"pass" if passes else "fail"}">{text}</span>'


def metric_table(table: dict, cfg: dict) -> str:
    """Every statistic of one simulated run, against what the real backtest did.

    Args:
        table: What metrics.table() returned — one entry per statistic.
        cfg: What config.load() returned, for the percentile set.

    Returns:
        A scrollable table, and a paragraph under it saying what each column is. `p` is the
        share of simulations that matched or beat the real backtest on that statistic's own
        good side, so a small p means the real one is hard to explain by chance; `bate a` is
        the complement read as a percentage of simulations it outperformed. For drawdown and
        the losing run both are computed on *less is better*, so a small p there means the
        real backtest suffered less than chance, not more.
    """
    qs = cfg["equity"]["percentiles"]
    alpha = cfg["diagnostics"]["alpha"]
    head = tables._row(["estadístico", "real", "mediana simulada", "p", "Bate a",
                        *[f"p{q:g}" for q in qs]], "th")
    body = []
    for name in metrics.TABLED:
        v = table[name]
        better = "más es mejor" if metrics.HIGHER_IS_BETTER[name] else "menos es mejor"
        body.append(tables._row([f"{metrics.LABELS[name]} <span class='hint'>({better})</span>",
                          charts.num(v["observed"]), charts.num(v["median"]),
                          _chip(f"{v['p_value']:.4f}", v["p_value"] <= alpha),
                          _chip(f"{v['beats']:.1%}", v["beats"] >= 1 - alpha),
                          *[charts.num(v["p"][q]) for q in qs]]))
    note = (f'<p class="lede"><b>p</b> — qué fracción de las simulaciones igualó o superó al '
            f'backtest real en ese indicador. Cuanto más pequeño, más difícil de explicar '
            f'por suerte; en verde cuando está en {alpha:.2f} o por debajo.<br>'
            f'<b>Bate a</b> — el porcentaje de simulaciones que el backtest real dejó atrás. '
            f'Es la otra cara del mismo número; en verde a partir del {1 - alpha:.0%}.<br>'
            f'En <b>Max drawdown</b> y <b>Longest losing run</b> los dos se calculan con '
            f'«menos es mejor», así que un p pequeño ahí significa que el backtest real '
            f'sufrió <i>menos</i> que el azar, no más.<br>'
            f'<b>p2,5 … p97,5</b> — los percentiles de la distribución simulada: entre p2,5 '
            f'y p97,5 cae el 95% de las simulaciones.</p>')
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>{note}'


def stats_block(view: dict, metric: str) -> str:
    """The four numbers the histogram marks, as a table beside it rather than on top of it.

    Args:
        view: What metrics.shape() returned for that statistic.
        metric: Which statistic, for its unit.

    Returns:
        A compact table. These used to be printed inside the SVG and collided with the real
        backtest's own label whenever the two landed near each other.
    """
    unit = f" {metrics.UNITS[metric]}" if metrics.UNITS[metric] else ""
    rows = [("Backtest real", view["observed"], "real"),
            ("Mediana simulada", view["median"], ""),
            ("p2,5 de las simulaciones", view["lo_ci"], ""),
            ("p97,5 de las simulaciones", view["hi_ci"], "")]
    body = "".join(tables._row([f'<span class="{cls}">{label}</span>' if cls else label,
                                charts.num(v) + unit]) for label, v, cls in rows)
    return f'<div class="scroll mini"><table>{body}</table></div>'


def beats_line(view: dict, metric: str) -> str:
    """The one sentence under the histogram: how many simulations the real backtest beat.

    Args:
        view: What metrics.shape() returned for that statistic.
        metric: Which statistic, for its name.

    Returns:
        An HTML block. The share reads the statistic's own direction, so it rises with a
        better strategy on every one of them: on drawdown it counts the simulations that
        suffered **more** than the real backtest, not the ones that scored higher.
    """
    worse = "sufrieron más" if not view["higher_is_better"] else "rindieron peor"
    return (f'<div class="beats"><b>{view["beats"]:.1%}</b> de las simulaciones {worse} que '
            f'el backtest real en <b>{metrics.LABELS[metric]}</b>.</div>')


def random_view(record: dict, cfg: dict, feed: str, model: str, metric: str) -> str:
    """One market under one null model: the equity cone, one metric's histogram, the table.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.
        feed: Which market.
        model: Which null model, a key of trade_models.MODELS.
        metric: Which statistic the histogram draws.

    Returns:
        The block the panel swaps in when any of the three selectors changes. Nothing is
        recomputed: every model's whole result was produced by the run and is held in memory.
    """
    run = record["runs"][feed][model]
    draws = cfg["nulls"]["draws"]
    return (f'<div class="pair">'
            + charts.cone(run["cone"], "Equity en calendario",
                          f"{feed} · {panel.NAMES[model]} · {draws:,} simulaciones",
                          charts.WIDE)
            + '<div>'
            + charts.distribution(run["shapes"][metric], metrics.LABELS[metric],
                                  f"{feed} · {draws:,} simulaciones", charts.NARROW)
            + stats_block(run["shapes"][metric], metric)
            + beats_line(run["shapes"][metric], metric) + '</div></div>'
            + metric_table(run["table"], cfg))


def random_tab(record: dict, cfg: dict) -> str:
    """Test 1a: the shell the panel fills, with its market and model sub-tabs.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's controls. The figures themselves arrive from /api/random, so switching
        market, model or metric never leaves the page or recomputes anything.
    """
    draws = cfg["nulls"]["draws"]
    return (f'<div class="note">{draws:,} backtests aleatorios <b>por cada mercado y cada '
            f'modelo</b>, valorados con las mismas posiciones y los mismos costes que el '
            f'real. Elige el mercado arriba, la forma de aleatorizar debajo, y el indicador '
            f'en el desplegable. Qué hace cada modelo, en la pestaña «Modelos».</div>'
            '<div class="subtabs" id="mkTabs"></div>'
            '<div class="subtabs sub2" id="mdTabs"></div>'
            '<div class="tools"><label>Indicador</label><select id="metricPick"></select>'
            '</div><div id="randomView"></div>')


def models_view(record: dict, cfg: dict, metric: str) -> str:
    """One bar per null model per market, for whichever statistic the reader picked.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.
        metric: Which statistic the p-values are for.

    Returns:
        The block the panel swaps in when the dropdown changes. Until this was selectable the
        chart showed `mean_r` and said so nowhere, which made the number unreadable.
    """
    out = []
    for feed, by_model in record["runs"].items():
        bars = [{"model": panel.NAMES[m], "p": by_model[m]["table"][metric]["p_value"]}
                for m in cfg["nulls"]["models"]]
        out.append(f"<h3><code>{feed}</code></h3>"
                   + figures.models(bars, cfg["diagnostics"]["alpha"],
                                    metrics.LABELS[metric]))
    return "".join(out)


def models_tab(record: dict, cfg: dict) -> str:
    """What the four ways of randomising are, and where they disagree.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML: a statistic picker over one bar chart per market, then a paragraph on
        each model saying what it adds over the one before it, and a closing note on the
        model that was retired and why. Where they disagree, the disagreement is the finding
        — it names the assumption the result needed.
    """
    models = cfg["nulls"]["models"]
    options = "".join(f'<option value="{k}">{metrics.LABELS[k]}</option>'
                      for k in metrics.TABLED)
    out = [f'<div class="note">Cada modelo corre sus <b>{cfg["nulls"]["draws"]:,} '
           f'simulaciones propias</b> en cada mercado, sobre la ventana del backtest. No hay '
           f'una única forma correcta de convertir un backtest en uno aleatorio, y la '
           f'respuesta se mueve con la elección: por eso se corren varios y manda el que '
           f'cambia exactamente una cosa. El p que sale en el Resumen es el de '
           f'<b>{panel.NAMES[cfg["nulls"]["headline"]]}</b> sobre '
           f'<b>{metrics.LABELS["mean_r"]}</b>.</div>',
           f'<div class="tools"><label>p de qué indicador</label>'
           f'<select id="modelMetric">{options}</select></div>',
           '<div id="modelsView"></div>',
           "<h2>Qué hace cada modelo</h2>"]
    for i, m in enumerate(models):
        first = (' <span class="tagline">el que manda en el Resumen</span>'
                 if m == cfg["nulls"]["headline"] else "")
        out.append(f'<div class="model"><h3>{panel.NAMES[m]}{first}</h3>'
                   f'<p class="lede"><code>{m}</code> · aleatoriza {panel.RANDOMISES[m]}</p>'
                   f'<p>{panel.EXPLAINED[m]}</p></div>')
    out.append(f'<div class="note">{panel.RETIRED}</div>')
    return "".join(out)


def stress_tab(record: dict, cfg: dict) -> str:
    """Cost and execution: the gradient, the breakeven, and the degraded-run distributions.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML. The cone here is what a worse broker can do to the same trades, not
        what random timing can — a different question from the random-entry tab's.
    """
    rows = pd.DataFrame(record["rows"])
    s = cfg["stress"]
    out = [figures.bars_by_market(
        [{"market": r["feed"], "breakeven": r["breakeven"]} for r in record["rows"]],
        "breakeven", "Múltiplo de coste de equilibrio (referencia del estudio: 2,0)", rule=2.0),
        tables.cost_table(rows),
        f'<div class="note">Debajo, las mismas operaciones ejecutadas peor {s["sims"]:,} veces: '
        f'{s["p_skip"]:.0%} de entradas perdidas, coste entre {s["cost_shock"][0]:.1f}x y '
        f'{s["cost_shock"][1]:.1f}x, y {s["fill_frac"]:.0%} de operaciones devolviendo el '
        f'{s["fill_depth"]:.0%} de su propia excursión adversa.</div>']
    for feed, by_model in record["runs"].items():
        run = by_model["stress"]
        out.append(f"<h3><code>{feed}</code></h3>")
        out.append(charts.cone(run["cone"], f"Equity bajo ejecución degradada — {feed}",
                               "el backtest real sobre el cono de las versiones degradadas"))
        out.append(metric_table(run["table"], cfg))
        for name in ("net", "ret_dd", "dd", "pf"):
            out.append(charts.distribution(run["shapes"][name], metrics.LABELS[name],
                                           f"{feed} · {s['sims']:,} ejecuciones degradadas"))
    return "".join(out)
