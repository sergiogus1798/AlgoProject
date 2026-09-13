"""Family D's section: regime luck — where in time and in market state the edge lived."""

from strategies.monteCarlo import barcharts, charts, gates, overlay, panel, regime, timeline
from strategies.monteCarlo.familypage.common import family_header


def family_d(result: dict, verdict: dict, cfg: dict) -> list[str]:
    """Regime luck: where in time and in market state the edge lived.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks.
    """
    q = cfg["global"]["report_percentile"]
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
        family_header("D", verdict),
        '<p class="lede">Las familias A a C dan por hecho que el edge es el mismo siempre. '
        'Ésta lo ataca: mira dónde vivió, en el calendario y en la volatilidad del mercado.</p>',
        barcharts.bars([w["start"][:7] for w in over], [w["net_5"] for w in over],
                    f"Ventanas móviles de {cfg['family_d']['window_months']} meses",
                    f"percentil 5 del beneficio en cada ventana · "
                    f"{gates.passing(over):.0%} en positivo"),
        "<h3>Bloques que no se solapan</h3>",
        '<p class="lede">Las ventanas solapadas suavizan; estos bloques no comparten ni una '
        'operación, así que un periodo malo de verdad aparece aquí y no allí.</p>',
        panel.table(["Desde", "Operaciones", "Mediana", "Percentil 5", "PF p5"], rows),
        "".join(charts.distribution(w["shape"], f"Beneficio remuestreado — bloque desde "
                                    f"{w['start']}", "",
                                    "Beneficio neto de la simulación, en $")
                for w in blocks if w["shape"] is not None),
        timeline.equity_windows(d["equity"], "Curva de equity con las ventanas marcadas",
                                "cada línea discontinua abre un bloque de la tabla de arriba"),
        "<h3>Régimen de volatilidad</h3>",
        f'<p class="lede">{d["regime"]["model"]}, en terciles. Cortes en '
        f'{d["regime"]["edges"][0]:,.2f} y {d["regime"]["edges"][1]:,.2f}; cobertura '
        f'{d["regime"]["coverage"]:.1%}. {d["regime"]["note"]}</p>',
        timeline.regime_series(d["regime"]["series"], "Precio y volatilidad, por tercil",
                               "pasa el ratón por una línea para resaltarla"),
        barcharts.bars(list(regime.BUCKETS), [buckets[b]["median_net"] for b in regime.BUCKETS],
                    "Beneficio mediano remuestreado por tercil de volatilidad",
                    f"el {d['regime']['concentration']:.0%} del beneficio sale de un tercil"),
        panel.table(["Tercil", "Operaciones", "Beneficio real", "Mediana", "Percentil 5",
                     "PF p5"], bucket_rows),
        "".join(charts.distribution(buckets[b]["shape"], f"Beneficio remuestreado — tercil "
                                    f"{b}", "", "Beneficio neto de la simulación, en $")
                for b in regime.BUCKETS),
        "<h3>El peor camino posible</h3>",
        '<p class="lede">Cosiendo un mal tramo de cada bloque de '
        f'{cfg["family_d"]["window_months"]} meses en uno solo. Qué tan malo es "malo" no '
        'tiene una respuesta de principio, así que se enseña a varias severidades en vez de '
        'elegir una — si el drawdown apenas se mueve entre columnas, la referencia es '
        'estable; si se dispara, esa inestabilidad ya es un hallazgo. No es un veto: es una '
        'referencia de estrés.</p>',
        panel.table(["Percentil por bloque", "Drawdown", "Beneficio neto", "Bloques cosidos"],
                    [[f"{q_ * 100:.0f}%", f"{v['dd_pct']:.1%}", f"{v['net']:,.0f} $",
                     f"{v['segments']}"] for q_, v in d["stitch"].items()]),
        f'<div class="note">Para comparar: el drawdown real fue {result["observed"]["dd_pct"]:.1%} '
        f'y el percentil 95 reordenando (Familia A) es {result["A"]["dd_pct_95"]:.1%}.</div>',
        barcharts.bars([str(k) for k in d["calendar"]["month"]],
                    list(d["calendar"]["month"].values()), "Beneficio por mes del año",
                    "sólo diagnóstico: con doce meses, el mejor de un reparto al azar ya "
                    "parece notable"),
        "<h3>Degradación dentro / fuera de muestra</h3>",
        '<p class="lede">Mismo remuestreo i.i.d. que la Familia B, repetido aquí porque esta '
        'familia es la que mira el tiempo: el número no cambia, solo el sitio en el que se '
        'lee.</p>',
        overlay.section(result["degrade"]["D"], "Beneficio remuestreado — IS vs OOS",
                        "Beneficio neto de la simulación, en $", q)]
