"""One sentence per config.yaml knob, for the drawer's hover text."""

TIPS = {
    "ingest.capital": "La cuenta contra la que se miden los drawdowns. Es la convención de SQX, "
                      "no una elección: cambiarla deja de reproducir sus tablas.",
    "fragility.cvar_alpha": "Qué parte de la cola entra en el drawdown condicional. 0.05 es la "
                            "media del 5% de peores re-ejecuciones.",
    "fragility.confidence": "Confianza de los intervalos exactos sobre los cuantiles.",
    "fragility.band_levels": "Los percentiles que dibuja el abanico de equity.",
    "modes.dip_alpha": "Umbral del test del dip. Por debajo, la distribución se declara bimodal.",
    "modes.min_outcome_share": "Proporción de simulaciones que deben dar resultados distintos "
                               "antes de aplicar cualquier test de forma. Spread y slippage se "
                               "muestrean de una rejilla y no lo pasan: no son distribuciones.",
    "attribution.control_task": "La tarea que hace de suelo de ruido. Todo efecto se mide en "
                                "sigmas de ésta.",
    "attribution.min_control_sigma": "Por debajo de esto, un efecto es ruido y no un hallazgo.",
    "evidence.method": "by = Benjamini-Yekutieli, no asume independencia. bh = Hochberg, la asume.",
    "evidence.alpha": "Tasa de falsos descubrimientos que se acepta tras corregir.",
    "evidence.ranks_min_strategies": "Estrategias mínimas para medir la estabilidad del ranking. "
                                     "Con menos, tau de Kendall no es medible y no se imprime.",
    "gates.min_pf": "Profit factor mínimo en el percentil 5 del estrés combinado.",
    "gates.survival_dd_pct": "Drawdown condicional que la cuenta se supone que aguanta. "
                             "**Sin calibrar contra tu operativa.**",
    "gates.collapse_frac": "Por debajo de esta fracción de las operaciones originales, la "
                           "estrategia dejó de ser ella misma.",
    "gates.exec_keep_frac": "Beneficio que la peor prueba de ejecución debe dejar en pie.",
    "gates.psr_gate": "Probabilidad mínima de que la ventaja no sea cero.",
    "scoring.weights": "Cuánto pesa cada rol. La producción vale más de la mitad porque es la "
                       "única estimación real; el control pesa cero porque es el denominador.",
    "scoring.tiers": "Cortes de la nota compuesta para STRONG / ACCEPTABLE / MARGINAL."}
