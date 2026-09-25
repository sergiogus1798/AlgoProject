"""The tabs of the tests that need no placement model, and of the execution stress."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.transfer.crossmarket.contract import shared
from studies.transfer.crossmarket.simulate import metrics

REFERENCE = {"block": "bloques de 6m"}
STRESSED = ("net", "ret_dd", "dd", "sharpe", "pf")


def reference_name(key: object) -> str:
    """How one of simulate/paired.py's reference windows reads; a number is a half-width."""
    return REFERENCE.get(key, f"centrada ±{key}m")


def paired_tab(record: dict) -> dict:
    """Test 1b: each trade against the exact mean of every same-length window around it."""
    rows, base = pd.DataFrame(record["rows"]), record["base"]
    return envelope.tab("paired", "Pareado (1b)", [
        shared.bars("Alfa de timing por operación, en puntos básicos",
                    [(r.feed, r.paired_bps) for r in rows.itertuples()], "bps", 0.0),
        blocks.table("El alfa en todas sus unidades", pd.DataFrame(
            [[r.feed, r.paired_bps, r.paired_pct, r.paired_r, r.paired_usd, r.paired_usd_total,
              r.paired_beat, r.paired_ci_lo * 1e4, r.paired_ci_hi * 1e4, r.paired_p]
             for r in rows.itertuples()],
            columns=["mercado", "alfa (bps)", "alfa (%)", "alfa (R)", "USD / operación",
                     "USD acumulado", "% de operaciones que ganan", "CI 5 % (bps)",
                     "CI 95 % (bps)", "p (Wilcoxon)"]),
            f"Referencia: en el activo base {base['feed']}, donde se optimizó, p = "
            f"{base['paired_p']:.4f} con {base['paired_beat']:.1%} de operaciones ganando a su "
            f"ventana media. Eso dice que el código mide lo que dice medir, nada de la "
            f"estrategia."),
        blocks.table("¿Depende de cómo se define «el mismo tramo»?", pd.DataFrame(
            [[r.feed, reference_name(s["reference"])
              + (" (la de la tabla)" if s["reference"] == r.paired_reference else ""),
              s["bps"], s["usd_total"], s["beat_share"], s["p"]]
             for r in rows.itertuples() for s in r.paired_sensitivity],
            columns=["mercado", "referencia", "alfa (bps)", "USD acumulado", "% que ganan",
                     "p (Wilcoxon)"]),
            "Un p que sobrevive a las cuatro definiciones no depende de ella; uno que sólo "
            "sobrevive a una la tenía de muleta.")],
        note="Dado que esta estrategia iba a estar N velas dentro, ¿eligió N velas mejores que "
             "las N velas medias de ese mismo tramo? El coste aparece en los dos lados y se "
             "cancela: no dice si gana dinero, sólo si sus entradas eligen momento. Es el único "
             "test sin modelo nulo ni suposición de coste.")


def exposure_tab(record: dict) -> dict:
    """Test 1c: were the bars it occupied better than the market's average bar?"""
    rows = pd.DataFrame(record["rows"])
    return envelope.tab("exposure", "Exposición (1c)", [
        shared.bars("Exceso por vela sobre la vela media, por unidad de riesgo",
                    [(r.feed, r.risk_normalised) for r in rows.itertuples()], "", 0.0),
        blocks.table("A, E y sus intervalos", pd.DataFrame(
            [[r.feed, r.risk_normalised, r.a, r.a_ci_lo, r.a_ci_hi, r.e,
              "no acotado" if not r.e_ci["bounded"] else
              f'[{r.e_ci["lo"]:+.2f}, {r.e_ci["hi"]:+.2f}]', r.mu_t, r.e_ci["sign_flip"]]
             for r in rows.itertuples()],
            columns=["mercado", "A / unidad de riesgo", "A (exceso por vela)", "A CI 5 %",
                     "A CI 95 %", "E", "CI 90 % de E (Fieller)", "deriva (t)",
                     "réplicas con deriva ≤ 0"]))],
        note="1b mide por operación contra el mismo tramo; 1c mide por vela contra toda la "
             "muestra y no descuenta el régimen. A resta la vela media y existe siempre; E "
             "divide por ella y, donde la deriva no se distingue de cero, su intervalo sale "
             "no acotado.")


def stress_tab(record: dict, cfg: dict) -> dict:
    """The same trades under a worse broker: breakeven, decay, and the degraded runs."""
    rows = pd.DataFrame(record["rows"])
    body = [shared.bars("Múltiplo de coste de equilibrio",
                        [(r.feed, r.breakeven) for r in rows.itertuples()], "× coste", 2.0,
                        "La línea es 2,0, la referencia del estudio."),
            blocks.table("Breakeven y decaimiento", pd.DataFrame(
                [[r.feed, r.breakeven, r.bar_shift_decay,
                  r.slippage_decay.get("0.25", next(iter(r.slippage_decay.values())))]
                 for r in rows.itertuples()],
                columns=["mercado", "breakeven (× coste)", "decaimiento 1 vela",
                         "decaimiento slippage 25 %"])),
            blocks.table("De dónde salen los supuestos", pd.DataFrame(
                [[r.feed, r.costs["charged"], r.costs["modelled"], r.costs["gap"],
                  f'{r.stress_settings["cost_shock"][0]:.1f}x – '
                  f'{r.stress_settings["cost_shock"][1]:.1f}x',
                  r.stress_settings["fill_depth"],
                  "sin declarar en execution.yaml" if not r.costs["declared"] else
                  r.costs["source"] + ("" if r.costs["reviewed"] else " · sin revisar")]
                 for r in rows.itertuples()],
                columns=["mercado", "coste cobrado (mediana USD)", "coste modelado (USD)",
                         "diferencia", "multiplicador de coste", "profundidad de fill (MAE)",
                         "origen"]),
                "El coste cobrado es un hecho recuperado del export; el modelado es un "
                "supuesto de execution.yaml. p_skip no se calibra desde ningún dato.")]
    for feed, runs in record["runs"].items():
        run = runs["stress"]
        body.append({**shared.cone(run["cone"], f"Equity bajo ejecución degradada — {feed}"),
                     "select": {"mercado": feed}})
        body.append({**shared.metric_table(run["table"], cfg, f"Ejecución degradada — {feed}"),
                     "select": {"mercado": feed}})
        body += [{**shared.distribution(run["shapes"][m], m, f"{metrics.LABELS[m]} — {feed}"),
                  "select": {"mercado": feed, "estadístico": metrics.LABELS[m]}}
                 for m in STRESSED]
    feeds = list(record["runs"])
    return envelope.tab(
        "stress", "Coste y ejecución", body,
        selectors=[{"key": "mercado", "label": "Mercado", "options": feeds,
                    "default": feeds[0] if feeds else ""},
                   {"key": "estadístico", "label": "Estadístico",
                    "options": [metrics.LABELS[m] for m in STRESSED],
                    "default": metrics.LABELS["net"]}],
        note="¿Cuánto sobrevive a un bróker peor? Las entradas son las reales: no se pregunta "
             "si valían algo, sino qué valen las mismas operaciones ejecutadas peor.")


def fingerprint_tab(record: dict) -> dict:
    """What the strategy does on each market against what it does on the base asset."""
    rows, base = pd.DataFrame(record["rows"]), record["base"]["feed"]
    body = [blocks.table("La huella, mercado a mercado", pd.DataFrame(
        [[r.feed, fp["holding_ks"]["p"], fp["excursion"]["mae"]["mean"],
          fp["excursion"]["mfe"]["mean"], fp["capture"]["median"], fp["shape"]["skew"],
          fp["shape"]["kurtosis"], fp["shape"]["tail_ratio"]]
         for r in rows.itertuples() for fp in [r.fingerprint]],
        columns=["mercado", f"KS duraciones vs {base} (p)", "MAE media (×ATR)",
                 "MFE media (×ATR)", "captura de MFE (mediana)", "skew", "kurtosis",
                 "tail ratio"]),
        "Aquí una p baja es un aviso: distribuciones de duración distintas. MAE y MFE en "
        "múltiplos del ATR de entrada, para comparar mercados de volatilidad distinta. "
        "Captura: qué parte de la excursión favorable acabó siendo beneficio — mide la salida.")]
    for r in rows.itertuples():
        for h in r.fingerprint["hists"]:
            edges = [h["lo"] + (h["hi"] - h["lo"]) * (i + 0.5) / len(h["market"])
                     for i in range(len(h["market"]))]
            body.append({"kind": "lines", "title": f"{h['label']} — {r.feed} frente a {base}",
                         "unit": "fracción", "x": [round(e, 4) for e in edges],
                         "series": [{"label": r.feed, "values": h["market"], "role": "real"},
                                    {"label": base, "values": h["base"], "role": "reference"}],
                         "note": f"{h['unit']}; eje recortado en el percentil 99 de los dos.",
                         "select": {"mercado": r.feed}})
    feeds = list(rows.feed)
    return envelope.tab(
        "fingerprint", "Huella", body,
        selectors=[{"key": "mercado", "label": "Mercado", "options": feeds,
                    "default": feeds[0] if feeds else ""}],
        note=f"¿Hace en este mercado lo mismo que en {base}, o hace otra cosa que también "
             f"gana? Todo es descriptivo, contra el activo base y nunca contra el azar.")
