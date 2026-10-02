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

    ("crossmarket", "reason"): "La frase del veredicto: cuántos mercados de cuántos tienen la "
                               "esperanza por encima de cero, contra el umbral.",
    ("crossmarket", "markets"): "Mercados en los que se pudo leer la estrategia.",
    ("crossmarket", "cleared"): "Mercados cuyo intervalo 5–95 % de la esperanza por operación, "
                                "ya con coste, queda entero por encima de cero.",
    ("crossmarket", "fraction"): "Mercados superados entre mercados leídos, de 0 a 1. Por "
                                 "debajo de 0,5 la estrategia se descarta.",
    ("crossmarket", "under_alpha"): "Mercados con p de 0,05 o menos contra Calendar Shift, que "
                                    "mueve cada operación semanas enteras dentro de su "
                                    "semestre. Se cuenta, no decide.",
    ("crossmarket", "paired_under_alpha"): "Mercados con p de 0,05 o menos en Timing Alpha: "
                                           "cada operación contra todas las ventanas de su "
                                           "duración cerca de ella. Dice si sus entradas eligen "
                                           "momento; se cuenta, no decide.",
    ("crossmarket", "edge_r"): "Mediana entre mercados del retorno medio por operación real "
                               "menos el mediano de los backtests al azar (Calendar Shift), en "
                               "ATR mediano de cada mercado. Positivo = entra mejor que el "
                               "azar.",
    ("crossmarket", "worst_pf"): "Profit Factor del peor mercado, sobre los retornos por "
                                 "operación que Python reconstruye en sus barras con su coste.",
    ("crossmarket", "median_pf"): "Mediana del Profit Factor entre mercados, con el mismo "
                                  "cálculo que el peor.",
    ("crossmarket", "pf_cv"): "Desviación típica del Profit Factor entre mercados. Baja = se "
                              "comporta parecido en todos; alta = uno o dos mercados con suerte "
                              "cargan el resultado. Vacía con un solo mercado.",

    ("edgeCost", "edge_mean"): "Beneficio bruto medio por operación (antes de spread y "
                               "comisión) entre el coste medio por operación que se modela hoy "
                               "(spread declarado del activo más comisión). Se juzga contra 2.",
    ("edgeCost", "edge_median"): "Lo mismo con la mediana del bruto: muy por debajo del edge "
                                 "medio, unas pocas operaciones grandes sostienen la media.",
    ("edgeCost", "n"): "Operaciones leídas.",

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
