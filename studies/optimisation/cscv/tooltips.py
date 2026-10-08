"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "cscv.blocks": "Bloques en que se corta la historia; 16 dan C(16,8) = 12.870 "
                   "particiones.",
    "cscv.seed": "Semilla de todo lo aleatorio: el mismo resultado con cualquier número de "
                 "procesos.",
    "panel.floor_per_param": "Operaciones mínimas en toda la historia por parámetro vivo: "
                             "con 6 vivos y 15, una variante necesita 90.",
    "panel.floor_per_year": "Operaciones mínimas por año en toda la historia.",
    "panel.min_variants": "Con menos variantes que éstas tras los filtros, el paso dice "
                          "«sin dato» y queda en LIMBO.",
    "null.draws": "Sorteos del nulo por madre y por tipo (neto, bruto y cada Sharpe "
                  "plantado). Más sorteos sólo afinan los percentiles del nulo.",
    "null.block_weeks": "Longitud media, en semanas, de los bloques del remuestreo.",
    "null.median_low": "Si la mediana del PBO del nulo cae por debajo, el estudio avisa de "
                       "que el remuestreo falla.",
    "null.median_high": "Si la mediana del PBO del nulo cae por encima, el estudio avisa de "
                        "que el remuestreo falla.",
    "power.deltas": "Sharpe anual que se planta en el control positivo, uno por curva.",
    "power.share": "Fracción de las variantes que recibe el Sharpe plantado.",
    "state.p_perdida_fail": "NO PASA si la elegida pierde fuera en esta fracción de las "
                            "particiones o más.",
    "state.p_perdida_null_pct": "LIMBO si la elegida pierde fuera más veces que este "
                                "percentil de la P de pérdida de su propio nulo.",
    "dominance.tolerance": "Cuánto puede subir la distribución de la elegida sobre la del "
                           "azar y contar aún como dominancia de primer orden.",
    "dominance.bins": "Barras del histograma sobre el que se lee la dominancia.",
    "dominance.reach": "Hasta dónde llega el histograma, en errores estándar de un Sharpe "
                       "de media muestra.",
    "perf.workers": "Procesos de la cola; nunca más que los núcleos físicos.",
    "perf.chunk": "Mitades de un CSCV que se puntúan a la vez.",
    "perf.budget_s": "Segundos de reloj a partir de los cuales el informe avisa de que la "
                     "cola se pasó del presupuesto."}
