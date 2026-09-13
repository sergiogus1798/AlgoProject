"""Family A's section: order luck — the same trades, in another order."""

from strategies.monteCarlo import charts, overlay, panel, sweeps
from strategies.monteCarlo.familypage.common import LABELS, family_header, fmt


def family_a(result: dict, verdict: dict, band: dict, cfg: dict) -> list[str]:
    """Order luck: the same trades, in another order.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
        band: What fan.envelope() returned for the headline model.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks.
    """
    q = cfg["global"]["report_percentile"]
    a_ = result["A"]
    rows = [[result["titles"][label], *[fmt(m, s[m]["p"][q]) for m in LABELS]]
            for label, s in a_["runs"].items()]
    seen = ["Backtest", *[fmt(m, result["observed"][m]) for m in LABELS]]
    drift = max(a_["invariant"].values())
    return [
        "<h2>Familia A — suerte de orden</h2>",
        family_header("A", verdict),
        '<p class="lede">Las mismas operaciones, en otro orden. El beneficio no cambia; el '
        'drawdown y las rachas sí. Lo que mide es cuánto del drawdown cómodo del backtest fue '
        'el orden en que llegaron.</p>',
        panel.table([f"Modelo (percentil {q})", *LABELS.values()], [seen, *rows]),
        f'<div class="note">Comprobación: barajar sin reemplazo (i.i.d. y bloques) movió el '
        f'beneficio neto en {drift:.2e} $ — cero, como debe ser: son permutaciones puras, '
        f'todas las operaciones exactamente una vez, así que su beneficio no puede moverse.'
        f'</div>',
        '<div class="note"><b>El bootstrap estacionario es distinto por dentro.</b> No es una '
        'permutación: dibuja bloques de longitud variable (media geométrica alrededor del '
        'tamaño de bloque) que pueden solaparse o dar la vuelta al final de la serie, así que '
        'una misma operación puede aparecer más de una vez y otra ninguna. Por eso su '
        'beneficio neto, a diferencia de «barajado» y «bloques barajados», <b>sí</b> se mueve '
        'de simulación en simulación — es el precio de no imponer una única longitud de '
        'dependencia, y es también la fila que da el drawdown de cabecera del informe.</div>',
        charts.distribution(a_["shape"], "Drawdown máximo reordenando",
                            f"percentil 95 (fijo, no cfg.report_percentile): "
                            f"{a_['dd_pct_95']:.2%} · backtest "
                            f"{result['observed']['dd_pct']:.2%} · inflación "
                            f"{a_['inflation']:.2f}×", "Drawdown, como % de la cuenta",
                            pct=True),
        charts.cone(band, "A dónde llegaba la curva en otro orden",
                    f"{result['titles'][sweeps.HEADLINE].lower()}, "
                    f"{len(band['observed'])} puntos"),
        "<h3>Cada modelo, por separado</h3>",
        '<p class="lede">El mismo drawdown reordenado, un histograma por cada tamaño de '
        'bloque y cada modelo — para ver si un bloque concreto se comporta distinto, no solo '
        'la media de todos.</p>',
        "".join(charts.distribution(shapes["dd_pct"], f"Drawdown — {result['titles'][label]}",
                                    "", "Drawdown, como % de la cuenta", pct=True)
                for label, shapes in a_["shapes"].items() if label != sweeps.HEADLINE),
        "<h3>Degradación dentro / fuera de muestra</h3>",
        overlay.section(result["degrade"]["A"], "Drawdown reordenando — IS vs OOS",
                        "Drawdown, como % de la cuenta", q, pct=True)]
