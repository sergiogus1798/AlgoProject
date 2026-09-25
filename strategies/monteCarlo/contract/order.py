"""Families A and B as tabs: order luck (the same trades reordered) and composition luck."""

import pandas as pd

from core.study import blocks, result as envelope
from strategies.monteCarlo.contract import headline, shapes
from strategies.monteCarlo.inputs import config
from strategies.monteCarlo.verdict import confidence


def family_a(result: dict, verdict: dict, band: dict, cfg: dict) -> dict:
    """Order luck: the same trades in another order move the drawdown, never the profit."""
    q = cfg["global"]["report_percentile"]
    a = result["A"]
    drift = max(a["invariant"].values())
    table = blocks.table(
        f"Cada modelo al percentil {q}",
        shapes.by_model(a["runs"], result["titles"], q, ("Backtest", result["observed"])),
        f"Comprobación: barajar sin reemplazo movió el beneficio neto en {drift:.2e} $, cero "
        f"como debe ser. El bootstrap estacionario sí lo mueve: dibuja bloques de longitud "
        f"variable que pueden repetir operaciones, y es la fila que da el drawdown de "
        f"cabecera.")
    head = shapes.distribution(
        a["shape"], None, "dd_pct", "Drawdown máximo reordenando",
        f"Percentil 95: {a['dd_pct_95']:.2%} · backtest {result['observed']['dd_pct']:.2%} · "
        f"inflación {a['inflation']:.2f}×.")
    per_model = [shapes.distribution(s["dd_pct"], a["runs"][k]["dd_pct"], "dd_pct",
                                     f"Drawdown — {result['titles'][k]}")
                 for k, s in a["shapes"].items() if k != config.HEADLINE]
    return envelope.tab(
        "familyA", "Familia A — suerte de orden",
        [headline.fired(verdict, "A"), table, head,
         shapes.cone(band, "A dónde llegaba la curva en otro orden",
                     f"{result['titles'][config.HEADLINE]}: bandas 2,5–97,5 y 25–75."),
         *per_model, *shapes.overlay(result["degrade"]["A"], "Drawdown reordenando")],
        note="Las mismas operaciones, en otro orden. El beneficio no cambia; el drawdown y "
             "las rachas sí. Mide cuánto del drawdown cómodo del backtest fue el orden en "
             "que llegaron.")


def family_b(result: dict, verdict: dict, cfg: dict) -> dict:
    """Composition luck: resampled with replacement, so which trades happened can change."""
    b = result["B"]
    table = blocks.table("Cada modelo al percentil 5",
                         shapes.by_model(b["runs"], result["titles"], 5))
    head = shapes.distribution(
        b["shape"], None, "net", "Beneficio neto remuestreando",
        f"Percentil 5: {b['net_5']:,.0f} $ · PF percentil 5 {b['pf_5']:.2f}. Quitando la "
        f"mejor operación el beneficio baja de {result['observed']['net']:,.0f} $ a "
        f"{b['outlier']['net_without_best']:,.0f} $, el {b['outlier']['share']:.0%} del "
        f"total.")
    per_model = [shapes.distribution(s["net"], b["runs"][k]["net"], "net",
                                     f"Beneficio — {result['titles'][k]}")
                 for k, s in b["shapes"].items() if k != config.BASELINE]
    samples = pd.DataFrame(
        [[name, v["n"], v["sharpe"], v["net"], v["pf_5"], confidence.average(v["n"])]
         for name, v in b["samples"].items()],
        columns=["muestra", "operaciones", "Sharpe mediano", "beneficio mediano (USD)",
                 "PF p5", "confianza"])
    ratio = b["oos_ratio"]
    return envelope.tab(
        "familyB", "Familia B — suerte de composición",
        [headline.fired(verdict, "B"), table, head, *per_model,
         blocks.table("Dentro y fuera de muestra", samples,
                      (f"El Sharpe fuera de muestra es el {ratio:.0%} del de dentro. "
                       if ratio == ratio else "")
                      + "No detecta sobreajuste: compara el nivel."),
         *shapes.overlay(result["degrade"]["B"], "Beneficio remuestreado")],
        note="Se vuelven a sortear las operaciones con reemplazo: aquí sí cambia el "
             "beneficio. Responde a cuánto del resultado descansa en unas pocas operaciones "
             "concretas.")
