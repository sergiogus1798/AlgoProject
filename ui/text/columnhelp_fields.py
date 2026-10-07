"""The «?» of every study column that is not a verdict and not a family, keyed (study, field).

Each sentence follows the code that writes the field: the study's `summary`/`verdict.csv` row
(`many.py`, `one.py`, `contract/`, `verdict/`). The percentile and sizing families live in
`columnhelp.py`.
"""

PIECE = "Estado que escribió su propio estudio, sin rederivar: "

FIELDS = {
    ("blindJoint", "wfc"): PIECE + "pass = fiable, watch = indeciso, fail = no fiable.",
    ("blindJoint", "cscv"): PIECE + "pass con PBO hasta el 50 %, fail por encima.",
    ("blindJoint", "marketSurfaces"): PIECE + "pass = la región viaja, watch = a medias, "
                                              "fail = no viaja.",
    ("blindJoint", "wfm"): PIECE + "pass = predicts, watch = blind, fail = perverse.",

    ("cloud", "point"): "Dónde está la madre entre sus vecinas (a 2 escalones) por su Ret/DD en "
                        "build: plateau = su vecindad rinde parecido; spike = casi nada a su "
                        "alrededor se le acerca; middling = no destaca en su propia nube.",
    ("cloud", "surface"): "Forma de la superficie junto a la madre: smooth = función suave de "
                          "los parámetros; rough = vecinas inmediatas discrepan, el resultado "
                          "es en buena parte sorteo; off_centre = el óptimo suave está en otro "
                          "sitio.",
    ("cloud", "temporal"): "Tres lecturas año a año: broad o carried (la familia gana casi "
                           "todos los años, o unos la sostienen y en otros pierde entera); "
                           "persistent o reshuffled (el orden de las variantes sobrevive al año "
                           "siguiente, o se rebaraja); drift_low o drift_high (la región buena "
                           "se queda o se desplaza).",
    ("cloud", "variants"): "Variantes del lote que entran en la nube, tras quitar los canarios "
                           "y las de menos de 30 operaciones; la madre nunca se quita.",
    ("cloud", "dropped"): "Variantes quitadas antes de leer: los canarios, puestos a propósito "
                          "en los extremos de la rejilla, y las de menos de 30 operaciones.",
    ("cloud", "r2"): "R² de un modelo cuadrático del Ret/DD en build ajustado a la vecindad de "
                     "la madre, de 0 a 1: qué parte de las diferencias entre vecinas explican "
                     "los parámetros de forma suave.",
    ("cloud", "roughness"): "Desacuerdo entre vecinas sin suponer modelo: mediana de la "
                            "distancia de cada variante a la mediana de sus 8 más próximas, en "
                            "rangos intercuartílicos del Ret/DD. Alto = el sorteo pesa más que "
                            "los parámetros.",
    ("cloud", "gap"): "Sharpe anualizado de la P&L diaria de la madre sola menos el de un "
                      "reparto a partes iguales entre vecinas buenas y distantes. Muy positivo "
                      "= sus vecinas no reproducen buena parte de su ventaja (sobreajuste).",
    ("cloud", "rho_median"): "Mediana, entre años consecutivos, de la ρ de Spearman del Sharpe "
                             "de las variantes de un año con el siguiente. Cerca de 0, el orden "
                             "se rebaraja cada año y optimizarlo es optimizar ruido.",
    ("cloud", "drift_median"): "Mediana de cuánto se mueve de un año al siguiente el centro del "
                               "decil de mejores variantes, en fracción del rango explorado de "
                               "cada parámetro. Alto = la región buena se desplaza.",

    ("wfc", "score"): "ρ de Spearman entre el Net Profit dentro y fuera de muestra de las "
                      "variantes, de −1 a 1. Se decide con su intervalo del 95 %, no con el "
                      "punto: el umbral es 0,30.",
    ("cscv", "score"): "El PBO de la regla argmax, de 0 a 1 (0,13 es un 13 %); 0,5 es lo que "
                       "vale elegir al azar. Los informes recientes lo dejan aquí vacío y lo "
                       "dan en el veredicto.",

    ("marketSurfaces", "call"): "La lectura del estudio, la misma palabra que su veredicto.",
    ("marketSurfaces", "state"): "pass, watch o fail de esa lectura: viaja, a medias, no viaja.",
    ("marketSurfaces", "declared"): "Mercados que _markets.yaml declara para el activo: el "
                                    "denominador; uno que falte en el lote cuenta como no "
                                    "pasado.",
    ("marketSurfaces", "markets"): "Mercados presentes en el lote, el principal incluido.",
    ("marketSurfaces", "variants"): "Variantes distintas del lote leídas en las superficies.",
    ("marketSurfaces", "segments"): "Tramos de la historia en los que se compara cada par de "
                                    "mercados.",
    ("marketSurfaces", "costs_provisional"): "Verdadero si algún mercado se retesteó con costes "
                                             "aún provisionales en assets/: el coste puede "
                                             "reordenar una superficie, así que la lectura es "
                                             "provisional.",

    ("wfm", "rho"): "ρ media (por z de Fisher) de las celdas de la matriz entre el Ret/DD en "
                    "muestra de cada configuración elegida y el que dio en el tramo siguiente. "
                    "Negativa = lo que optimiza mejor va peor después.",
    ("wfm", "low"): "Extremo inferior del intervalo bootstrap al 95 % de esa ρ, remuestreando "
                    "celdas y no tramos. Optimista: las celdas reparten la misma historia.",
    ("wfm", "high"): "Extremo superior del intervalo bootstrap al 95 % de esa ρ, remuestreando "
                     "celdas y no tramos. Optimista: las celdas reparten la misma historia.",
    ("wfm", "cells"): "Celdas de la matriz (número de tramos × % fuera de muestra) con al menos "
                      "5 tramos utilizables.",
    ("wfm", "steps"): "Tramos walk-forward sumados en esas celdas.",
    ("wfm", "share_negative"): "Fracción de celdas con ρ negativa, de 0 a 1.",
    ("wfm", "share_changed"): "Mediana de la fracción de parámetros que el optimizador cambia de "
                              "un tramo al siguiente, de 0 a 1.",
    ("wfm", "drift_high"): "Verdadero si esa fracción llega a 0,5: cada reoptimización elige una "
                           "estrategia sustancialmente distinta. Junto a blind o perverse es lo "
                           "coherente, no un segundo hallazgo.",

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
