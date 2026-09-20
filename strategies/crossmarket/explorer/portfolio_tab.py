"""The Portfolio tab: does adding this market break the combination, or only fail to help it?

The narrow question the cross-market retest raises on its own. It is not portfolio
construction — that lives in portfolio/ — and it is not a substitute for strategies/monteCarlo,
which asks how much of one stream is luck."""

from strategies.crossmarket.mechanics.curves import COMBINED
from strategies.crossmarket.render import overlays, overview, svg
from strategies.crossmarket.simulate import metrics

# What the marginal table compares. Ret/DD first: it is the one a market can quietly wreck
# while still looking profitable on its own.
SHOWN = ("ret_dd", "net", "dd", "sharpe", "pf", "losing_run")


def marginal_table(marginal: list[dict], whole: dict) -> str:
    """What the combination loses when each market is taken out of it.

    Args:
        marginal: What portfolio.marginal() returned.
        whole: The combined account's own statistics.

    Returns:
        A scrollable table. Read the Δ columns: **a positive Δ means the market improves the
        combination**, because Δ is the whole minus the portfolio without it. A market whose
        Δ Ret/DD is negative is costing the combination more than it brings, whatever its own
        p-value said.
    """
    head = overview._row(["se quita…", "operaciones",
                          *[f"{metrics.LABELS[k]} sin él" for k in SHOWN],
                          *[f"Δ {metrics.LABELS[k]}" for k in SHOWN]], "th")
    body = []
    for m in marginal:
        body.append(overview._row(
            [f'<code>{m["feed"]}</code>', f'{m["trades"]:,}',
             *[svg.num(m["without"][k]) for k in SHOWN],
             *[f'<span class="{"ok" if m["delta"][k] > 0 else "no"}">'
               f'{svg.num(m["delta"][k])}</span>' for k in SHOWN]]))
    body.append(overview._row(
        ["<b>el portfolio entero</b>", "", *[svg.num(whole[k]) for k in SHOWN],
         *["" for _ in SHOWN]]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def interval_table(ci: dict, whole: dict) -> str:
    """The combined account's statistics with their calendar-block intervals.

    Args:
        ci: What portfolio.resampled() returned.
        whole: The combined account's own statistics.

    Returns:
        A scrollable table.
    """
    head = overview._row(["estadístico", "portfolio real", "mediana remuestreada",
                          "CI 90%"], "th")
    body = [overview._row([metrics.LABELS[k], svg.num(whole[k]),
                           svg.num(ci[k]["median"]),
                           f'[{svg.num(ci[k]["lo"])}, {svg.num(ci[k]["hi"])}]'])
            for k in SHOWN]
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def equity_figure(record: dict, cfg: dict) -> str:
    """The combined account's curve with every market's contribution to it underneath.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        One figure. The thick line is the account; the thin ones are what each market put into
        it, in the **same** account, so they add up to it. That is deliberately not the main
        tab's chart, where every market has an independent account and the heights compare
        nothing — here a market below zero all sample is one the others were carrying.

        There is no percentile cone on it. The resampling draws whole calendar blocks in a
        drawn order, so its paths do not live on the calendar this axis uses; the uncertainty
        is in the interval table below instead of in a band that would imply a timeline it
        does not have.
    """
    colours = {**overview_palette(record), COMBINED: "var(--ink)"}
    return overlays.equity(record["portfolio"]["curves"], colours, COMBINED,
                           "Equity del portfolio, y qué puso cada mercado en él",
                           f'una sola cuenta de {cfg["equity"]["starting"]:,.0f} $ · '
                           "las líneas finas suman la gruesa · % de esa cuenta única",
                           lead_note="todos los mercados juntos")


def overview_palette(record: dict) -> dict[str, str]:
    """The same colour per market the rest of the panel uses.

    Args:
        record: What work.RESULTS holds.

    Returns:
        {feed: colour}. Imported through the main tab so a market cannot end up one colour
        here and another one there.
    """
    return svg.palette(list(record["equity"]), record["base"]["feed"])


def portfolio_tab(record: dict, cfg: dict) -> str:
    """One strategy in every market it traded, as a single account.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML: what the combination did, what each market contributes to it, how
        often its positions overlapped, and two different ways of asking how much of it is
        luck. No verdict — what counts as "breaking the portfolio" is the owner's line.
    """
    p, w = record["portfolio"], record["portfolio"]["whole"]
    weeks, base = cfg["portfolio"]["block_weeks"], record["base"]["feed"]
    tiles = [(svg.num(w["net"]) + " $", "beneficio del portfolio"),
             (f'{w["dd_pct"] * 100:.1f} %', "peor caída, sobre la curva combinada"),
             (f'{w["ret_dd"]:.2f}', "Ret/DD del portfolio"),
             (f'{p["overlap"]["share"]:.1%}', "del tiempo abierto, con 2+ posiciones"),
             (str(p["overlap"]["most"]), "posiciones a la vez, como máximo"),
             (f'{p["trades"]:,}', "operaciones en total")]
    return "".join([
        f'<div class="note"><b>Una sola cuenta de '
        f'{cfg["equity"]["starting"]:,.0f} $ para todos los mercados</b>, '
        f'<code>{base}</code> incluido como posición núcleo. La caída se calcula sobre la '
        f'curva <b>combinada</b>, nunca sumando las de cada mercado. El oro está dentro '
        f'porque la pregunta aquí es qué hace la combinación que operarías, y ésa lleva oro '
        f'— pero el oro es el activo sobre el que se optimizó, así que el portfolio base se ve '
        f'mejor de lo que es.</div>',
        '<div class="headline">'
        + "".join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>' for v, k in tiles)
        + "</div>",
        f'<p class="lede">{p["from"]} … {p["to"]} · {len(p["markets"])} mercados</p>',
        equity_figure(record, cfg),
        "<h2>Qué aporta cada mercado</h2>", marginal_table(p["marginal"], w),
        '<div class="note"><b>Ésta es la tabla por la que existe la pestaña.</b> Δ es el '
        'portfolio entero menos el portfolio sin ese mercado: <b>Δ positivo = ese mercado mejora '
        'la combinación</b>. Un mercado con Δ Ret/DD negativo le está costando al portfolio '
        'más de lo que le aporta, por muy bien que se vea su propio p-valor. Que un mercado '
        'aporte poco no es un problema; que reste, sí.</div>',
        f"<h2>Cuánto de esto es suerte</h2>",
        f'<p class="lede">Remuestreo por bloques de <b>{weeks} semanas de calendario</b>, no '
        f'por operaciones sueltas: la dependencia que importa en un portfolio es '
        f'<i>contemporánea</i> — dos mercados perdiendo la misma semana — y remuestrear '
        f'operación a operación destruiría justo lo que se quiere medir. Las operaciones de '
        f'todos los mercados dentro de un bloque viajan juntas.</p>',
        interval_table(p["ci"], w),
        "<h3>Y si hubieran llegado en otro orden</h3>",
        '<p class="lede">Las mismas operaciones, barajadas por bloques '
        '(<code>strategies.monteCarlo.model.draws</code>, que es de quien es esta familia). La '
        'composición no cambia, así que el beneficio es idéntico por construcción y sólo se '
        'mueven las métricas de camino: caída, racha y Ret/DD. Es la otra mitad de la '
        'pregunta — la de arriba cambia qué semanas ocurrieron, ésta sólo en qué orden.</p>',
        interval_from_table(p["order"])])


def interval_from_table(table: dict) -> str:
    """The reordering result, as the same three columns the interval table uses.

    Args:
        table: What metrics.table() returned for the reordered runs.

    Returns:
        A scrollable table. `net` is left in deliberately: seeing it identical to the real one
        is what shows the reordering changed nothing about composition.
    """
    head = overview._row(["estadístico", "portfolio real", "mediana barajada", "p2,5 – p97,5"],
                         "th")
    body = [overview._row([metrics.LABELS[k], svg.num(table[k]["observed"]),
                           svg.num(table[k]["median"]),
                           f'{svg.num(table[k]["p"][2.5])} – '
                           f'{svg.num(table[k]["p"][97.5])}'])
            for k in SHOWN if k in table]
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'
