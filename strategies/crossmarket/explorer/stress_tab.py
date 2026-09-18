"""The cost-and-execution tab: the same trades under a worse broker, per market.

Its assumptions come from execution.yaml through execution.settings(), not from a round number
in config.yaml — and the tab says, per market, which of the two it ended up using."""

import pandas as pd

from strategies.crossmarket import charts, figures, metrics, tables
from strategies.crossmarket.explorer.simulations import STRESSED, metric_table


def stress_tab(record: dict, cfg: dict) -> str:
    """Cost and execution: the gradient, the breakeven, and the degraded-run distributions.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML. The cone here is what a worse broker can do to the same trades, not
        what random timing can — a different question from the random-entry tab's. What
        "worse" means per market comes from execution.yaml rather than from a round number,
        and the assumptions table says where each figure came from and whether the owner has
        checked it.
    """
    rows = pd.DataFrame(record["rows"])
    out = ['<div class="lead"><h3>La pregunta</h3><p><i>¿Cuánto de esto sobrevive a un bróker '
           'peor?</i> Aquí las entradas son las reales: no se pregunta si valían algo, se '
           'pregunta qué valen las mismas operaciones ejecutadas peor.</p></div>',
           figures.bars_by_market(
               [{"market": r["feed"], "breakeven": r["breakeven"]} for r in record["rows"]],
               "breakeven", "Múltiplo de coste de equilibrio (referencia del estudio: 2,0)",
               rule=2.0),
           tables.cost_table(rows),
           "<h3>De dónde salen los supuestos</h3>",
           tables.assumptions_table(rows),
           '<div class="note"><b>El coste cobrado es un hecho; el modelado es un supuesto.</b> '
           'El primero se recupera operación a operación del propio export de SQX. El segundo '
           'sale de <code>execution.yaml</code>, que hoy lleva valores de ejemplo hasta que el '
           'dueño ponga los de su bróker. <code>p_skip</code> no se calibra desde ningún dato: '
           'nada en el export dice cuántas órdenes se habrían perdido, así que sigue siendo un '
           'supuesto explícito.</div>']
    for feed, by_model in record["runs"].items():
        run, s = by_model["stress"], rows.loc[rows.feed == feed, "stress_settings"].iloc[0]
        out.append(f"<h3><code>{feed}</code></h3>")
        out.append(f'<p class="lede">{s["sims"]:,} ejecuciones degradadas · '
                   f'{s["p_skip"]:.0%} de entradas perdidas · coste entre '
                   f'{s["cost_shock"][0]:.1f}x y {s["cost_shock"][1]:.1f}x · '
                   f'{s["fill_frac"]:.0%} de operaciones devolviendo el '
                   f'{s["fill_depth"]:.0%} de su propia excursión adversa · '
                   f'{"calibrado desde execution.yaml" if s["calibrated"] else "sin calibrar"}'
                   f'</p>')
        out.append(charts.cone(run["cone"], f"Equity bajo ejecución degradada — {feed}",
                               "el backtest real sobre el cono de las versiones degradadas"))
        out.append(metric_table(run["table"], cfg))
        for name in STRESSED:
            out.append(charts.distribution(run["shapes"][name], metrics.LABELS[name],
                                           f"{feed} · {s['sims']:,} ejecuciones degradadas"))
    return "".join(out)
