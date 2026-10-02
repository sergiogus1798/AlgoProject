"""One sentence per config.yaml knob, for the drawer's hover text."""

TIPS = {
    "ingest.cents_per_usd": "Céntimos por dólar: el .bin de SQX guarda el resultado de cada "
                            "operación en céntimos enteros.",
    "ingest.workers": "Procesos que leen las simulaciones a la vez; cambia RAM por tiempo "
                      "(16 tarda 1,9 s y ocupa 1,9 GB en 40 runs).",
    "ingest.min_sims": "Simulaciones mínimas de una tarea para que sus cuantiles se lean.",
    "ingest.compression": "Compresión de los ficheros intermedios que escribe la ingesta.",
    "levels": "Los niveles de confianza que produce SQX; son los únicos que existen.",
    "recon.tolerance": "Diferencia relativa máxima entre una métrica reconstruida y la de SQX.",
    "recon.absolute_floor": "Por debajo de esta diferencia absoluta manda el redondeo a "
                            "céntimos y la métrica se da por igual.",
    "recon.systematic_share": "Si una métrica falla en esta parte de los runs es una "
                              "fórmula mal hecha y la ingesta se para; por debajo, la celda se "
                              "excluye y se apunta.",
    "scenario.ordering_metric": "La métrica que ordena las simulaciones cuando un nivel se lee "
                                "como un escenario.",
    "scenario.show_levels": "Los niveles que se enseñan como escenario.",
    "fragility.fan_points": "Puntos de progreso normalizado del abanico de equity: las "
                            "simulaciones tienen longitudes distintas.",
    "fragility.n_resamples": "Remuestreos BCa para los estadísticos suaves; un cuantil usa el "
                             "intervalo exacto.",
    "attribution.dispersion_center": "Centro de la dispersión: median es Brown-Forsythe, "
                                     "robusto; mean sería Levene, que aquí no lo es.",
    "ingest.capital": "La cuenta contra la que se miden los drawdowns. Es la convención de SQX, "
                      "no una elección: cambiarla deja de reproducir sus tablas.",
    "fragility.cvar_alpha": "Qué parte de la cola entra en el drawdown condicional. 0.05 es la "
                            "media del 5% de peores re-ejecuciones.",
    "fragility.confidence": "Confianza de los intervalos exactos sobre los cuantiles.",
    "fragility.band_levels": "Los percentiles que dibuja el abanico de equity.",
    "fragility.fan_sample": "Cuántas curvas individuales se guardan por tarea, repartidas de "
                            "peor a mejor por su equity final — no en orden de simulación —, "
                            "para que una muestra pequeña siga cubriendo todo el rango "
                            "(feedback 2026-09-30 §6: histogramas y equity curves por tarea).",
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
