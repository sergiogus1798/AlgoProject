"""The «?» of every study column that is not a verdict and not a family, keyed (study, field).

Each sentence follows the code that writes the field: the study's `summary`/`verdict.csv` row
(`many.py`, `one.py`, `contract/`, `verdict/`). The percentile and sizing families live in
`columnhelp.py`.
"""

PIECE = "Estado que escribió su propio estudio, sin rederivar: "

FIELDS = {
    ("blindJoint", "wfc"): PIECE + "pass = PASA (sin fallo: elegir por el pasado no "
                              "lleva a algo que pierda fuera), watch = LIMBO (indeciso), "
                              "fail = NO PASA (fallo).",
    ("blindJoint", "cscv"): PIECE + "pass = PASA (no descarta), watch = LIMBO, fail = NO PASA "
                                    "(la elegida pierde fuera en demasiadas particiones).",
    ("blindJoint", "marketSurfaces"): PIECE + "pass = PASA, watch = LIMBO (sin dato, prima "
                                              "baja u oos2 perverso), fail = NO PASA (el "
                                              "orden entre mercados es perverso).",
    ("blindJoint", "wfm"): PIECE + "pass = PASA, watch = LIMBO, fail = NO PASA (L1 pierde en "
                                   "oos2 más de lo que explica el ruido).",

    ("cloud", "variants"): "Variantes del lote que entran en el mapa de parámetros, tras quitar "
                           "los controles, los duplicados exactos y las que no llegan al suelo "
                           "de operaciones; la madre nunca se quita.",
    ("cloud", "live"): "Parámetros vivos: los que se mueven en el lote. Con k vivos la superficie "
                       "cuadrática tiene 1 + 2k + k(k−1)/2 coeficientes.",
    ("cloud", "r2_adj"): "R² ajustado de la superficie cuadrática del exceso por año en build, "
                         "de 0 a 1 como mucho: qué parte de las diferencias entre variantes "
                         "explican los parámetros, descontando los coeficientes usados. Es una "
                         "fracción de varianza, no un porcentaje de acierto.",
    ("cloud", "r2_ref"): "El R² ajustado que da el ruido puro: se baraja el exceso entre las "
                         "variantes y se toma el percentil configurado de los R² ajustados "
                         "resultantes. El mapa sólo se lee por encima de él.",
    ("cloud", "legible"): "Sí si el R² ajustado real supera su referencia barajada: el ranking "
                          "de parámetros (Sobol) se puede leer. No = sin estructura "
                          "distinguible del ruido. Diagnóstico: no corta nada.",

    ("wfc", "composicion"): "La composición que decide el estado: c1 = build+oos1 dentro, oos2 "
                            "fuera. Las otras dos (c2 = build → oos1+oos2, c3 = build → oos2) "
                            "se miden y se anotan al lado.",
    ("wfc", "estado"): "PASA, LIMBO o NO PASA de la composición que decide. PASA: el top que "
                       "elegiría un optimizador gana fuera y el orden no es perverso; es un "
                       "veto levantado, no un voto a favor. LIMBO: gana pero optimizar empeora, "
                       "o no hay dato. NO PASA: el top no gana fuera.",
    ("wfc", "orden"): "Positivo, neutro o perverso: si el orden de las variantes por exceso "
                      "dentro se repite fuera más de lo que da el ruido (p+ ≤ α), no dice nada, "
                      "o va al revés (p− ≤ α, lo mejor de dentro es lo peor de fuera).",
    ("wfc", "fuerte"): "Un orden positivo con ρ igual o mayor que el 0,30 de Tinsley. Es una "
                       "etiqueta: no cambia el estado.",
    ("wfc", "n"): "Variantes medidas, tras quitar controles, duplicados exactos y las que no "
                  "llegan a los suelos de operaciones.",
    ("wfc", "rho"): "ρ de Spearman entre el exceso por año de dentro y el de fuera, variante a "
                    "variante, de −1 a +1: +1 mismo orden, 0 ningún parecido, −1 invertido. Es "
                    "un coeficiente, no un porcentaje.",
    ("wfc", "p_mas"): "Fracción de sorteos del nulo de volteo con una ρ igual o mayor que la "
                      "observada. Pequeño (≤ α) = el orden se repite fuera más que por ruido.",
    ("wfc", "p_menos"): "Fracción de sorteos del nulo con una ρ igual o menor que la observada. "
                        "Pequeño (≤ α) = lo mejor de dentro tiende a ser lo peor de fuera.",
    ("wfc", "nivel_top"): "Mediana del exceso por año fuera de las variantes del top de dentro. "
                          "Por encima de 0, lo que elegiría un optimizador gana fuera.",
    ("wfc", "r_sel"): "Retención de la prima de selección: (nivel del top − nivel de todas) "
                      "fuera ÷ lo mismo dentro. 1 = se conserva entera; 0 = elegir no sirve; "
                      "negativo = selección perversa. Vacío si la prima de dentro es casi nula.",
    ("wfc", "p_nivel"): "Fracción de sorteos del nulo de volteo cuya mediana del top es igual o "
                        "mayor que la observada. Sólo se anota: el estado ya no depende de él.",
    ("wfc", "fines_de_semana"): "Fracción de operaciones fuera de muestra cerradas lunes o martes "
                                "tras un fin de semana abierto. Si es alta el nulo se repite con "
                                "bloques de dos semanas (aviso, no cambia el estado).",
    ("wfc", "orden_bloque"): "El orden (positivo, neutro, perverso) releído con bloques de dos "
                             "semanas en el nulo: si cambia, el resultado depende de cómo se "
                             "agrupan las semanas.",
    ("wfc", "descuadre_sqx"): "Variantes cuyo beneficio neto recalculado difiere del NetProfit "
                              "de SQX más allá de la tolerancia: la única comprobación de los "
                              "costes reconstruidos.",
    ("wfc", "wfc.c1.estado"): "PASA, LIMBO o NO PASA de c1 (build+oos1 → oos2), el que juzga el "
                              "piloto: el hecho `wfc.c1.estado` del paso 17.",
    ("wfc", "score"): "ρ de Spearman de la composición que decide, de −1 a +1. Es un "
                      "coeficiente, no un porcentaje; se lee contra su nulo (p+, p−), no contra "
                      "un umbral fijo.",
    ("crossTF", "seen"): "Sharpe por operación, sin anualizar, de la hermana escalada en ese "
                         "timeframe: el estadístico que se juzga.",
    ("crossTF", "p"): "p empírico contra el nulo que sólo cambia cuándo entra cada operación, en "
                      "las barras de ese timeframe. Por debajo de 0,05 es «survives».",
    ("crossTF", "baseline"): "Sharpe por operación de la madre en su propio timeframe: la "
                             "referencia del control.",
    ("crossTF", "control"): "Sharpe por operación de la hermana escalada corrida en el "
                            "timeframe original. Si pierde más de la mitad de la referencia, "
                            "la culpa es del cambio de parámetros (control_failed).",
    ("crossTF", "reading"): "La lectura de la celda: la misma palabra que el veredicto de ese "
                            "timeframe.",
    ("crossTF", "trades"): "Operaciones de la hermana escalada en ese timeframe. Con 0 la "
                           "lectura es silent: no operar no es fallar.",

    ("crossmarket", "markets"): "Mercados de la lista de la estrategia, válidos o no.",
    ("crossmarket", "markets_valid"): "Mercados que pasan los controles previos (precios alineados, "
                                      "valor del punto y costes bien). Sólo con ellos se prueba.",
    ("crossmarket", "invalid_fraction"): "Parte de la lista que no se pudo usar. Si pasa del 25 % "
                                         "la prueba entera queda en duda.",
    ("crossmarket", "fixed_distance"): "Cuántos parámetros de la estrategia son distancias fijas "
                                       "en puntos o pips (un stop de 50 puntos). No significan lo "
                                       "mismo en otro mercado. 0 = ninguno.",
    ("crossmarket", "freq_off"): "Mercados donde la estrategia opera con una frecuencia muy distinta "
                                 "a la esperable por su mercado principal: su regla no se traslada.",
    ("crossmarket", "freq_off_fraction"): "Mercados con otra frecuencia entre mercados válidos, de 0 "
                                          "a 1.",
    ("crossmarket", "z_conj"): "Cuántas desviaciones del azar gana la estrategia sumando todos los "
                               "mercados. El azar son sus mismas entradas movidas semanas enteras. "
                               "2,33 ≈ una probabilidad del 1 % de que sea suerte.",
    ("crossmarket", "p_conj"): "Probabilidad de que el azar iguale o supere el resultado conjunto "
                               "real. Cuanto más baja, menos parece suerte.",
    ("crossmarket", "z_conj_v2"): "La z conjunta sólo en V2, los años de oos1 del principal: años "
                                  "que el generador no vio. Negativa = dejó de funcionar ahí.",
    ("crossmarket", "z_conj_v0"): "La z conjunta en V0, los años anteriores al build del principal. "
                                  "Anotada, no juzga.",
    ("crossmarket", "z_conj_v1"): "La z conjunta en V1, los años del build del principal, donde la "
                                  "estrategia se ajustó. Anotada, no juzga.",
    ("crossmarket", "z_minus_market"): "La z conjunta más baja que sale al quitar, de uno en uno, cada "
                                       "mercado. Alta = no cuelga de un solo mercado.",
    ("crossmarket", "minus_market"): "El mercado cuya retirada baja más la z conjunta.",
    ("crossmarket", "p_breadth"): "Probabilidad de que tantos mercados salgan a favor sólo por suerte. "
                                  "Baja = la ventaja se repite en más mercados de lo que daría el azar.",
    ("crossmarket", "breadth_count"): "Mercados donde la estrategia gana más que el azar en su "
                                      "mediana.",
    ("crossmarket", "tau_half"): "Ventaja por operación que mantiene en la mitad de los mercados, "
                                 "como parte de la que tiene en el principal. Vacía hasta que el paso 8 "
                                 "entregue la ventaja del principal.",
    ("crossmarket", "e_principal"): "Ventaja por operación de la estrategia en su mercado principal "
                                    "(el denominador de P7). Vacía hasta que la entregue el paso 8.",
    ("crossmarket", "worse"): "Mercados donde la estrategia va claramente peor que el azar (z de ese "
                              "mercado de −1,65 o menos).",
    ("crossmarket", "worse_fraction"): "Mercados en contra entre mercados válidos, de 0 a 1.",
    ("crossmarket", "z_beta"): "Cuántas desviaciones se aparta del azar la pendiente de su ventaja año "
                               "a año. Muy negativa = la ventaja se apaga con el tiempo.",
    ("crossmarket", "e_end"): "Ventaja por operación que la tendencia anual estima para el último año. "
                              "Positiva = al final aún queda ventaja.",
    ("crossmarket", "beta"): "Cuánto cambia por año la ventaja por operación, en R. Anotada.",
    ("crossmarket", "e_end_ratio"): "Ventaja estimada del último año entre la ventaja media de todos los "
                                    "años. Anotada.",
    ("crossmarket", "net_t_pooled"): "t semanal del neto de SQX sumado en los mercados válidos. Anotada, "
                                     "no juzga: no usa las corridas al azar.",
    ("crossmarket", "trades"): "Operaciones de la estrategia en los mercados válidos.",

    ("edgeCost", "edge_mean"): "Beneficio bruto medio por operación (antes de costes) entre el "
                               "coste medio que pagó, sólo en oos1 y con el repreciado común "
                               "(el mismo número que la puerta). Se juzga contra 2.",

    ("mcRetest", "composite"): "Puntuación de 0 a 100: media ponderada de producción, "
                               "ejecución, especificación y datos, cada una la peor de sus "
                               "tareas. Con un veto, FAIL sea cual sea.",
    ("mcRetest", "binding"): "La subpuntuación más baja, la que limita: production (estrés "
                             "combinado), execution (spread, slippage, distancia mínima), "
                             "specification (parámetros, salidas) o data (histórico movido).",
    ("mcRetest", "stress_net_p5"): "Percentil 5 del beneficio neto entre las re-ejecuciones del "
                                   "estrés combinado (todas las perturbaciones a la vez), en "
                                   "dinero de la cuenta. Con 0 o menos veta: el 5 % peor no "
                                   "gana.",
    ("mcRetest", "stress_cvar_dd_pct"): "Media del drawdown máximo % del 5 % de peores "
                                        "re-ejecuciones del estrés combinado (CVaR): lo que "
                                        "pasa cuando pasa lo malo. Pasado el límite de la "
                                        "cuenta, veta.",
    ("mcRetest", "vetoes"): "Los vetos que dispararon y fuerzan FAIL (beneficio no robusto, "
                            "drawdown insostenible, colapso de régimen, edge indistinguible de "
                            "cero, ejecución frágil, sobreajuste de parámetros). Vacío = ninguno.",
    ("mcRetest", "blocked_by"): "Los vetos de datos que dejan el juicio en INCONCLUSIVE: una "
                                "tarea sin dispersión, una tabla de niveles corrupta o una "
                                "reconciliación fallida. No se pudo juzgar; no es un fallo.",
}
