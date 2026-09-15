"""One sentence per config.yaml knob, for the config drawer's hover text."""

TIPS = {
    "nulls.draws": "Backtests aleatorios por mercado y modelo. El p-valor más pequeño que se "
                   "puede observar es 1/(draws+1): con 5.000, 0,0002.",
    "nulls.seed": "Semilla fija y compartida entre mercados, así un mismo sorteo es el mismo "
                  "desplazamiento en todos ellos.",
    "nulls.block_months": "Longitud del bloque de régimen dentro del cual se mueve cada "
                          "operación. Trece años de oro no son un solo régimen: un nulo "
                          "repartido por toda la muestra le regala a la estrategia la deriva "
                          "del tramo alcista en el que caen sus operaciones.",
    "nulls.models": "Qué modelos nulos se corren. El primero es el que lee el panel por "
                    "defecto; los demás se leen al lado para ver de qué suposición dependía "
                    "el resultado.",
    "nulls.replicate_friday": "Recorta cada duración aleatoria en el cierre del viernes, "
                              "igual que la regla de salida recorta la real. Sin esto, una "
                              "operación colocada un viernes por la tarde se queda abierta "
                              "un fin de semana que la real nunca aguantó.",
    "nulls.min_hold": "Una operación que abre y cierra en la misma vela no es una operación.",
    "sweep.windows": "Tamaños de bloque del barrido: «full» es un solo bloque (el modelo tal "
                     "cual corre arriba), «3y» tres años, «6m» seis meses. Cada operación sólo "
                     "se recoloca dentro de su propio bloque: encogerlo devuelve el régimen y "
                     "nada más.",
    "sweep.models": "Los modelos que se barren. Sólo tienen sentido los de colocación libre: "
                    "Calendar Shift ya fija el régimen por construcción.",
    "sweep.reference": "El modelo cuyo p se dibuja como línea horizontal en cada gráfico del "
                       "barrido.",
    "sweep.min_months": "Tamaño mínimo en meses. Un tamaño más corto no se calcula.",
    "sweep.min_trades": "Un bloque con menos operaciones reales que esto es débil: barajar, "
                        "remuestrear o ajustar una distribución a tan pocas no describe nada.",
    "sweep.min_free_share": "Un bloque con menos de esta fracción de sus velas libre es débil: "
                            "sus operaciones sólo pueden volver más o menos a donde estaban, y "
                            "un nulo que reproduce el real da p ≈ 0,5 haya acierto o no.",
    "sweep.max_weak_share": "Si los bloques débiles de un tamaño tienen más de esta fracción "
                            "de las operaciones, ese tamaño no se calcula: sale como ✕ en vez "
                            "de con un p engañoso.",
    "sweep.evidence_drop": "Órdenes de magnitud que tiene que subir p del tamaño más ancho al "
                           "más estrecho para etiquetar la curva «creciente → régimen». 1 es "
                           "multiplicarse por diez.",
    "strata.atr_bins": "Sólo para regime_strata, que corre si lo añades a nulls.models: en "
                       "cuántos cuantiles de ATR se parten las velas.",
    "strata.trend_bars": "Sólo para regime_strata: velas sobre las que se lee el signo de la "
                         "tendencia, antes de que abra la vela.",
    "bootstrap.draws": "Remuestreos por cada intervalo de confianza.",
    "bootstrap.block": "Operaciones por bloque del bootstrap. Las velas dentro de una "
                       "operación están autocorrelacionadas, así que remuestrear operación a "
                       "operación sueltas estrecharía el intervalo de mentira.",
    "bootstrap.ci": "Percentiles que se reportan como intervalo. [5, 95] es un IC del 90%.",
    "exposure.mu_min_t": "|t| mínimo de la deriva del propio mercado para que E se muestre. "
                         "E divide por esa deriva: en un mercado cuya deriva es "
                         "estadísticamente cero, E no significa nada, y en uno que cayó sale "
                         "negativo y se lee justo al revés de lo que es. Medido: Brent t = "
                         "−0,11 daba E = −69,4 siendo el mercado con más A de los tres.",
    "exposure.drop_zero_mfe": "Excluye las operaciones cuyo MFE es cero en vez de dividir "
                              "por él. Una operación que nunca se movió a favor tiene una "
                              "captura indefinida, no infinita.",
    "paired.alternative": "Lado del test de Wilcoxon. «greater» pregunta si las operaciones "
                          "reales baten a su ventana ciega, que es la hipótesis del estudio.",
    "drivers.hurst_lags": "Horizontes sobre los que se ajusta la pendiente del exponente de "
                          "Hurst. El número se mueve con este conjunto: léelo como un orden "
                          "entre mercados, no como una cifra de tres decimales.",
    "drivers.variance_ratio_q": "Horizonte de agregación del variance ratio de Lo-MacKinlay, "
                                "en velas. 1 es paseo aleatorio, más de 1 tendencia, menos "
                                "reversión.",
    "drivers.adx_period": "Periodo del ADX, con el suavizado de Wilder.",
    "drivers.adx_trend": "ADX por encima de este valor cuenta la vela como en tendencia.",
    "drivers.efficiency_window": "Velas sobre las que se mide el ratio de eficiencia de "
                                 "Kaufman: recorrido neto dividido por camino andado.",
    "stress.cost_multiples": "Múltiplos del coste a los que se vuelve a valorar todo, para "
                             "ver a partir de cuál desaparece el beneficio.",
    "stress.bar_shift": "Velas que se desplazan entrada y salida para ver cuánto decae el "
                        "resultado si la ejecución llega tarde.",
    "stress.slippage_fractions": "Fracción del rango de la vela que se cede en contra en "
                                 "cada extremo.",
    "diagnostics.alpha": "El nivel contra el que se colorean los p-valores. No decide nada: "
                         "aquí no hay veredicto, sólo un umbral de lectura.",
    "diagnostics.min_trades": "Por debajo de esto el mercado se marca como muestra pequeña. "
                              "No se excluye: sale con todos sus números y con el aviso.",
    "diagnostics.min_on_open": "Por debajo de esto hay órdenes pendientes entre las entradas, "
                               "que son una selección condicionada al precio que ningún nulo "
                               "reproduce. Se avisa, no se descarta el mercado.",
    "diagnostics.correlated": "Correlación supuesta entre mercados para la cifra honesta de "
                              "falsos positivos. Mercados movidos por el dólar se comportan "
                              "como muchos menos de los que son.",
    "diagnostics.pca_warn": "Porción de varianza en PC1 por encima de la cual estos mercados "
                            "son una sola apuesta y no varias confirmaciones.",
}

GROUPS = {"nulls": "Modelos nulos", "sweep": "Barrido de ventana",
          "strata": "Estratos de régimen", "bootstrap": "Bootstrap", "exposure": "Exposición (1c)",
          "paired": "Test pareado (1b)", "drivers": "Propiedades del mercado",
          "stress": "Coste y ejecución", "diagnostics": "Lectura y avisos"}
