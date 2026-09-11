"""The five family sections of a strategy's page: its tables, its figures and its verdict line."""

from strategies.monteCarlo import charts, confidence, gates, panel, regime, stress, sweeps

LABELS = {"net": "beneficio neto", "return_pct": "retorno", "dd": "drawdown $",
          "dd_pct": "drawdown %", "ret_dd": "Ret/DD", "sharpe": "Sharpe por operación",
          "pf": "profit factor", "losing_run": "racha perdedora"}
# stress.MODELS is code and stays in English; the report is read in Spanish.
MODELS_ES = {"skip": "entradas que el sistema real no llega a tomar",
             "cost_shock": "comisión y swap hasta el doble de lo que SQX cobró",
             "fill_degrade": "ejecuciones que devuelven parte de lo que la propia operación "
                             "ya había cedido",
             "spread_widen": "un spread más ancho que el fijo que supuso el backtest"}
MONEY = ("net", "dd")
SHARE = ("return_pct", "dd_pct")


def fmt(metric: str, value: float) -> str:
    """One statistic in the units it is read in.

    Args:
        metric: Key of LABELS.
        value: The number.

    Returns:
        A formatted cell.
    """
    if metric in MONEY:
        return f"{value:,.0f} $"
    if metric in SHARE:
        return f"{value:.2%}"
    return f"{value:,.2f}"


def family_a(result: dict, band: dict, cfg: dict) -> list[str]:
    """Order luck: the same trades, in another order.

    Args:
        result: What run.analyse() returned.
        band: What fan.envelope() returned for the headline model.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks.
    """
    q = cfg["global"]["report_percentile"]
    a_ = result["A"]
    rows = [[result["titles"][label], *[fmt(m, s[m]["p"][q]) for m in LABELS]]
            for label, s in a_["runs"].items()]
    seen = ["backtest", *[fmt(m, result["observed"][m]) for m in LABELS]]
    drift = max(a_["invariant"].values())
    return [
        "<h2>Familia A — suerte de orden</h2>",
        '<p class="lede">Las mismas operaciones, en otro orden. El beneficio no cambia; el '
        'drawdown y las rachas sí. Lo que mide es cuánto del drawdown cómodo del backtest fue '
        'el orden en que llegaron.</p>',
        panel.table([f"modelo (percentil {q})", *LABELS.values()], [seen, *rows]),
        f'<div class="note">Comprobación: reordenar sin reemplazo movió el beneficio neto en '
        f'{drift:.2e} $ — cero, como debe ser. Si no lo fuera, el modelo estaría cambiando la '
        f'composición y no sólo el orden.</div>',
        charts.distribution(a_["shape"], "Drawdown máximo reordenando",
                            f"percentil 95: {a_['dd_pct_95']:.2%} · backtest "
                            f"{result['observed']['dd_pct']:.2%} · inflación "
                            f"{a_['inflation']:.2f}×", "drawdown como fracción de la cuenta"),
        charts.cone(band, "A dónde llegaba la curva en otro orden",
                    f"{result['titles'][sweeps.HEADLINE].lower()}, "
                    f"{len(band['observed'])} puntos")]


def family_b(result: dict, cfg: dict) -> list[str]:
    """Composition luck: which trades occurred at all.

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks, including the IS/OOS level comparison.
    """
    q = cfg["global"]["report_percentile"]
    b = result["B"]
    rows = [[result["titles"][label], *[fmt(m, s[m]["p"][5]) for m in LABELS]]
            for label, s in b["runs"].items()]
    samples = [[name, f"{v['n']:,}", f"{v['sharpe']:.4f}", f"{v['net']:,.0f} $",
                f"{v['pf_5']:.2f}", confidence.average(v["n"])]
               for name, v in b["samples"].items()]
    return [
        "<h2>Familia B — suerte de composición</h2>",
        '<p class="lede">Se vuelven a sortear las operaciones con reemplazo: aquí sí cambia el '
        'beneficio. Responde a cuánto del resultado descansa en unas pocas operaciones '
        'concretas.</p>',
        panel.table(["modelo (percentil 5)", *LABELS.values()], rows),
        charts.distribution(b["shape"], "Beneficio neto remuestreando",
                            f"percentil 5: {b['net_5']:,.0f} $ · PF percentil 5 "
                            f"{b['pf_5']:.2f}", "beneficio neto de la simulación, en $"),
        f'<div class="note"><b>Dependencia de la mejor operación.</b> Quitándola, el beneficio '
        f'baja de {result["observed"]["net"]:,.0f} $ a {b["outlier"]["net_without_best"]:,.0f} $ '
        f'— el {b["outlier"]["share"]:.0%} del total.</div>',
        "<h3>Dentro y fuera de muestra</h3>",
        '<p class="lede">No detecta sobreajuste: compara el nivel. Una caída grande del Sharpe '
        'mediano al pasar a OOS es optimismo que el test de decaimiento no recogió.</p>',
        panel.table(["muestra", "operaciones", "Sharpe mediano", "beneficio mediano",
                     "PF p5", "confianza"], samples),
        f'<div class="note">El Sharpe fuera de muestra es el <b>{b["oos_ratio"]:.0%}</b> del de '
        f'dentro.</div>' if b["oos_ratio"] == b["oos_ratio"] else ""]


def family_c(result: dict, cfg: dict) -> list[str]:
    """Execution luck: worse fills, worse costs, missed entries.

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks.
    """
    fired = {f["test"] for f in gates.check(result, cfg) if f["family"] == "C"}
    rows = [[stress.TITLES[name], MODELS_ES[name], f"{v['median_net']:,.0f} $", f"{v['keep']:.0%}",
             f"{v['net_5']:,.0f} $", f"{v['pf_5']:.2f}",
             '<span class="no">falla</span>' if name in fired
             else '<span class="ok">pasa</span>']
            for name, v in result["C"].items()]
    return [
        "<h2>Familia C — suerte de ejecución</h2>",
        '<p class="lede">Las mismas operaciones peor ejecutadas: costes hasta el doble de los '
        'que SQX cobró, spread más ancho, entradas perdidas, y ejecuciones que devuelven parte '
        'de lo que cada operación ya había cedido en su peor momento (su propio MAE). Las '
        'cuatro tienen que pasar: no se promedian. Las cuatro se ejecutan siempre, aunque '
        'alguna ya haya fallado — igual que todas las demás pruebas del informe.</p>',
        panel.table(["prueba", "qué modela", "beneficio mediano", "queda", "beneficio p5",
                     "PF p5", ""], rows)]


def family_d(result: dict, cfg: dict) -> list[str]:
    """Regime luck: where in time and in market state the edge lived.

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks.
    """
    d = result["D"]
    over, blocks = d["overlapping"], d["nonoverlapping"]
    buckets = d["regime"]["buckets"]
    rows = [[w["start"], f"{w['n']:,}", f"{w['median_net']:,.0f} $", f"{w['net_5']:,.0f} $",
             f"{w['pf_5']:.2f}"] for w in blocks]
    bucket_rows = [[name, f"{v['n']:,}", f"{v['net']:,.0f} $", f"{v['median_net']:,.0f} $",
                    f"{v['net_5']:,.0f} $", f"{v['pf_5']:.2f}"]
                   for name, v in buckets.items()]
    return [
        "<h2>Familia D — suerte de régimen</h2>",
        '<p class="lede">Las familias A a C dan por hecho que el edge es el mismo siempre. '
        'Ésta lo ataca: mira dónde vivió, en el calendario y en la volatilidad del mercado.</p>',
        charts.bars([w["start"][:7] for w in over], [w["net_5"] for w in over],
                    f"Ventanas móviles de {cfg['family_d']['window_months']} meses",
                    f"percentil 5 del beneficio en cada ventana · "
                    f"{gates.passing(over):.0%} en positivo"),
        "<h3>Bloques que no se solapan</h3>",
        '<p class="lede">Las ventanas solapadas suavizan; estos bloques no comparten ni una '
        'operación, así que un periodo malo de verdad aparece aquí y no allí.</p>',
        panel.table(["desde", "operaciones", "mediana", "percentil 5", "PF p5"], rows),
        "<h3>Régimen de volatilidad</h3>",
        f'<p class="lede">{d["regime"]["model"]}, en terciles. Cortes en '
        f'{d["regime"]["edges"][0]:,.2f} y {d["regime"]["edges"][1]:,.2f}; cobertura '
        f'{d["regime"]["coverage"]:.1%}. {d["regime"]["note"]}</p>',
        charts.bars(list(regime.BUCKETS), [buckets[b]["median_net"] for b in regime.BUCKETS],
                    "Beneficio mediano remuestreado por tercil de volatilidad",
                    f"el {d['regime']['concentration']:.0%} del beneficio sale de un tercil"),
        panel.table(["tercil", "operaciones", "beneficio real", "mediana", "percentil 5",
                     "PF p5"], bucket_rows),
        "<h3>El peor camino posible</h3>",
        f'<div class="note">Cosiendo un mal tramo de cada bloque de '
        f'{cfg["family_d"]["window_months"]} meses — el percentil 5 de cada uno — el drawdown '
        f'llega a <b>{d["stitch"]["dd_pct"]:.1%}</b> de la cuenta, frente al '
        f'{result["observed"]["dd_pct"]:.1%} real y al {result["A"]["dd_pct_95"]:.1%} del '
        f'percentil 95 reordenando. No es un veto: es la referencia de estrés.</div>',
        charts.bars([str(k) for k in d["calendar"]["month"]],
                    list(d["calendar"]["month"].values()), "Beneficio por mes del año",
                    "sólo diagnóstico: con doce meses, el mejor de un reparto al azar ya "
                    "parece notable")]


def family_e(result: dict, cfg: dict) -> list[str]:
    """Significance: could the edge be zero, given N and the shape of the distribution?

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks.
    """
    e = result["E"]
    return [
        "<h2>Familia E — significación</h2>",
        '<p class="lede">La PSR pregunta si el edge podría ser cero, teniendo en cuenta cuántas '
        'operaciones hay y la forma de la distribución: la asimetría y las colas gordas entran '
        'en la cuenta, así que un sistema cuyo beneficio está en cuatro operaciones enormes '
        'saca menos PSR que otro con el mismo Sharpe repartido.</p>',
        panel.table(["qué", "valor"],
                    [["PSR", f"{e['psr']:.4f}"],
                     ["objetivo / veto", f"{cfg['family_e']['psr_target']:.2f} / "
                                         f"{cfg['family_e']['psr_gate']:.2f}"],
                     ["Sharpe por operación", f"{e['sharpe']:.4f}"],
                     ["asimetría / curtosis", f"{e['skew']:.2f} / {e['kurtosis']:.2f}"],
                     ["operaciones", f"{e['n']:,}"],
                     ["P(Sharpe>0) remuestreando", f"{e['bootstrap']:.4f}"],
                     ["diferencia analítica vs remuestreo", f"{e['gap']:.4f}"]]),
        '<div class="note">Las dos últimas filas son la comprobación cruzada: si coinciden, la '
        'conclusión no depende de la aproximación normal; si se separan, las operaciones son lo '
        'bastante asimétricas como para que sí dependa — y eso es un hallazgo, no un error.</div>',
        '<div class="note"><b>Aquí no hay Deflated Sharpe.</b> Necesitaría saber cuántas '
        'estrategias se probaron durante la generación. Ese número no existe en esta fase y '
        'fabricarlo daría una cifra creíble y falsa.</div>']
