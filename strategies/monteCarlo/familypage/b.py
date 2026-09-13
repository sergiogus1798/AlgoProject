"""Family B's section: composition luck — which trades occurred at all."""

from strategies.monteCarlo import charts, confidence, overlay, panel, sweeps
from strategies.monteCarlo.familypage.common import LABELS, family_header, fmt


def family_b(result: dict, verdict: dict, cfg: dict) -> list[str]:
    """Composition luck: which trades occurred at all.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
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
        family_header("B", verdict),
        '<p class="lede">Se vuelven a sortear las operaciones con reemplazo: aquí sí cambia el '
        'beneficio. Responde a cuánto del resultado descansa en unas pocas operaciones '
        'concretas.</p>',
        panel.table(["Modelo (percentil 5)", *LABELS.values()], rows),
        charts.distribution(b["shape"], "Beneficio neto remuestreando",
                            f"percentil 5: {b['net_5']:,.0f} $ · PF percentil 5 "
                            f"{b['pf_5']:.2f}", "Beneficio neto de la simulación, en $"),
        f'<div class="note"><b>Dependencia de la mejor operación.</b> Quitándola, el beneficio '
        f'baja de {result["observed"]["net"]:,.0f} $ a {b["outlier"]["net_without_best"]:,.0f} $ '
        f'— el {b["outlier"]["share"]:.0%} del total.</div>',
        "<h3>Cada modelo, por separado</h3>",
        '<p class="lede">El mismo beneficio remuestreado, un histograma por cada tamaño de '
        'bloque — el i.i.d. no tiene bloque, así que su composición cambia de la forma más '
        'agresiva posible; los de bloque grande se acercan más al backtest real.</p>',
        "".join(charts.distribution(shapes["net"], f"Beneficio — {result['titles'][label]}",
                                    "", "Beneficio neto de la simulación, en $")
                for label, shapes in b["shapes"].items() if label != sweeps.BASELINE),
        "<h3>Dentro y fuera de muestra</h3>",
        '<p class="lede">No detecta sobreajuste: compara el nivel. Una caída grande del Sharpe '
        'mediano al pasar a OOS es optimismo que el test de decaimiento no recogió.</p>',
        panel.table(["Muestra", "Operaciones", "Sharpe mediano", "Beneficio mediano",
                     "PF p5", "Confianza"], samples),
        f'<div class="note">El Sharpe fuera de muestra es el <b>{b["oos_ratio"]:.0%}</b> del de '
        f'dentro.</div>' if b["oos_ratio"] == b["oos_ratio"] else "",
        overlay.section(result["degrade"]["B"], "Beneficio remuestreado — IS vs OOS",
                        "Beneficio neto de la simulación, en $", q)]
