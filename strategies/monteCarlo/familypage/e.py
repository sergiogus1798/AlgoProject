"""Family E's section: significance — could the edge be zero, given N and its shape?"""

from strategies.monteCarlo import panel
from strategies.monteCarlo.familypage.common import family_header


def family_e(result: dict, verdict: dict, cfg: dict) -> list[str]:
    """Significance: could the edge be zero, given N and the shape of the distribution?

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks.
    """
    e = result["E"]
    return [
        "<h2>Familia E — significación</h2>",
        family_header("E", verdict),
        '<p class="lede"><b>La Probabilistic Sharpe Ratio (PSR)</b> es la probabilidad de que '
        'el Sharpe real de la estrategia sea mayor que un valor de referencia (aquí, cero) — '
        'no una probabilidad de ganar dinero, sino de que el edge observado no sea ruido. A '
        'diferencia de un contraste clásico, tiene en cuenta cuántas operaciones hay y la '
        'forma exacta de su distribución: la asimetría y las colas gordas entran en la '
        'cuenta, así que un sistema cuyo beneficio depende de cuatro operaciones enormes saca '
        'menos PSR que otro con el mismo Sharpe repartido entre muchas — el número castiga la '
        'concentración que el Sharpe por sí solo no ve.</p>',
        panel.table(["Qué", "Valor"],
                    [["PSR", f"{e['psr']:.4f}"],
                     ["Objetivo / veto", f"{cfg['family_e']['psr_target']:.2f} / "
                                         f"{cfg['family_e']['psr_gate']:.2f}"],
                     ["Sharpe por operación", f"{e['sharpe']:.4f}"],
                     ["Asimetría / curtosis", f"{e['skew']:.2f} / {e['kurtosis']:.2f}"],
                     ["Operaciones", f"{e['n']:,}"],
                     ["P(Sharpe>0) remuestreando", f"{e['bootstrap']:.4f}"],
                     ["Diferencia analítica vs remuestreo", f"{e['gap']:.4f}"]]),
        '<div class="note">Las dos últimas filas son la comprobación cruzada: si coinciden, la '
        'conclusión no depende de la aproximación normal; si se separan, las operaciones son lo '
        'bastante asimétricas como para que sí dependa — y eso es un hallazgo, no un error.</div>',
        '<div class="note"><b>Aquí no hay Deflated Sharpe.</b> Necesitaría saber cuántas '
        'estrategias se probaron durante la generación. Ese número no existe en esta fase y '
        'fabricarlo daría una cifra creíble y falsa.</div>',
        '<div class="note"><b>De dónde sale cada número.</b> PSR, Sharpe, asimetría y '
        'curtosis se calculan directamente sobre las operaciones reales del backtest, en su '
        'propio orden — no son el resultado de ninguna simulación, son una fórmula analítica '
        'aplicada una vez. <code>P(Sharpe&gt;0) remuestreando</code> es la única cifra '
        'simulada de esta familia: el percentil de Sharpes positivos en el mismo remuestreo '
        'i.i.d. que dibuja el histograma de la Familia B (mismas operaciones, mismo modelo, '
        'estadístico distinto). La fila de abajo compara ambas.</div>']
