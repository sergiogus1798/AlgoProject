"""One sentence per config.yaml knob, for the config drawer's hover text."""

TIPS = {
    "nulls.batch_draws": "Runs nulos por mercado en el lote de toda la exportación: su "
                         "veredicto lee el intervalo de la esperanza, no la p, y el nulo era "
                         "el 84 % de su CPU.",
    "nulls.batch_cells": "Máximo de runs × operaciones que el lote valora de una vez, unos "
                         "90 bytes cada una: es el mando de la memoria.",
    "nulls.headline": "El modelo nulo cuya p resume la tabla: block_shift es el único que cambia "
                      "una sola cosa, así que su p baja sólo se atribuye al momento de entrar.",
    "nulls.chunk": "Runs aleatorios valorados por tanda; es memoria, no estadística.",
    "equity.starting": "Cuenta, en USD, desde la que arranca la curva de equity aditiva.",
    "equity.steps": "Puntos por curva; un SVG no puede enseñar más.",
    "equity.bands": "Los percentiles del cono que se dibuja alrededor de la curva real.",
    "equity.percentiles": "Los percentiles que se dan en las tablas de métricas.",
    "verdict.breadth_floor": "Parte de los mercados cuyo intervalo de la esperanza tiene que "
                             "quedar por encima de cero para MANTENER la estrategia; es la única "
                             "criba que aplica este estudio.",
    "nulls.draws": "Backtests aleatorios por mercado y modelo. El p-valor más pequeño que se "
                   "puede observar es 1/(draws+1): con 5.000, 0,0002.",
    "nulls.seed": "Semilla fija: dos ejecuciones con la misma configuración dan los mismos "
                  "números. No acopla los mercados entre sí — cada uno consume su propio "
                  "generador con su propia forma, medido corr(sorteo) = -0,002.",
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
    "joint.pool": "Cómo se agregan los mercados fuera de muestra en el nulo conjunto. "
                  "«mean_r» promedia el estadístico crudo — correcto mientras las anchuras "
                  "del nulo de cada mercado estén dentro de un factor pequeño (medido 1,20 "
                  "entre Brent y plata). «z» promedia el estadístico estandarizado de cada "
                  "mercado, y es lo que hay que usar si uno tiene una anchura varias veces "
                  "mayor, o decide el veredicto él solo.",
    "strata.atr_bins": "Sólo para regime_strata, que corre si lo añades a nulls.models: en "
                       "cuántos cuantiles de ATR se parten las velas.",
    "strata.trend_bars": "Sólo para regime_strata: velas sobre las que se lee el signo de la "
                         "tendencia, antes de que abra la vela.",
    "bootstrap.draws": "Remuestreos por cada intervalo de confianza.",
    "bootstrap.block": "Operaciones por bloque del bootstrap. Las velas dentro de una "
                       "operación están autocorrelacionadas, así que remuestrear operación a "
                       "operación sueltas estrecharía el intervalo de mentira.",
    "bootstrap.ci": "Percentiles que se reportan como intervalo. [5, 95] es un CI del 90%.",
    "exposure.mu_min_t": "|t| mínimo de la deriva del propio mercado para que E se muestre. "
                         "E divide por esa deriva: en un mercado cuya deriva es "
                         "estadísticamente cero, E no significa nada, y en uno que cayó sale "
                         "negativo y se lee justo al revés de lo que es. Medido: Brent t = "
                         "−0,11 daba E = −69,4 siendo el mercado con más A de los tres.",
    "exposure.bar_block": "Velas por bloque del bootstrap pareado con el que se construye el "
                          "intervalo de Fieller de E. Bloques, y no velas sueltas, porque los "
                          "retornos de velas contiguas están autocorrelacionados.",
    "exposure.drop_zero_mfe": "Excluye las operaciones cuyo MFE es cero en vez de dividir "
                              "por él. Una operación que nunca se movió a favor tiene una "
                              "captura indefinida, no infinita.",
    "paired.alternative": "Lado del test de Wilcoxon. «greater» pregunta si las operaciones "
                          "reales baten a su ventana ciega, que es la hipótesis del estudio.",
    "paired.reference": "Cómo se define «el mismo tramo de mercado»: un número son los meses a "
                        "cada lado de la entrada (3 = ventana centrada de seis meses), y "
                        "«block» es la partición fija en semestres que usa Calendar Shift. La "
                        "centrada no tiene fronteras: con bloques, una operación que entra "
                        "tres días antes de que acabe el semestre se mide contra un tramo que "
                        "ya casi ha pasado.",
    "paired.sensitivity": "Todas las definiciones con las que se corre además el test, para "
                          "ver si el p depende de la elección. Un p que aguanta las cuatro no "
                          "depende de ella; uno que sólo aguanta una la tenía de muleta.",
    "equity.risk_target_dd": "Caída máxima a la que se reescala cada mercado para compararlos "
                             "a riesgo igual. 0,10 = cada mercado se dimensiona hasta que su "
                             "peor caída es el 10% de la cuenta.",
    "diagnostics.alpha": "El nivel contra el que se colorean los p-valores. No decide nada: "
                         "aquí no hay veredicto, sólo un umbral de lectura.",
    "diagnostics.min_trades": "Por debajo de esto el mercado se marca como muestra pequeña. "
                              "No se excluye: sale con todos sus números y con el aviso.",
    "diagnostics.min_on_open": "Por debajo de esto hay entradas ejecutadas a un precio que no "
                               "es el de su vela: una selección condicionada al precio que "
                               "ningún nulo reproduce. Se mide sobre el precio, descontando el "
                               "spread constante, nunca sobre el reloj. Se avisa, no se "
                               "descarta el mercado.",
    "diagnostics.fill_tolerance": "Cuánto puede separarse una entrada del spread constante del "
                                  "mercado y seguir contando como que tomó el precio de su "
                                  "vela, en múltiplos del ATR mediano. Medido, la desviación "
                                  "máxima real es 0,0045 ATR: un tick.",
    "diagnostics.max_fill_error": "Error mediano de precio por encima del cual las velas "
                                  "probablemente no son las del backtest, en múltiplos del ATR "
                                  "mediano. Un spread constante vive muy por debajo y no lo "
                                  "dispara.",
    "diagnostics.min_on_grid": "Por debajo de esta fracción de operaciones colocables en la "
                               "rejilla de velas salta un aviso. Una operación que abre y "
                               "cierra dentro de la misma vela no tiene intervalo, así que "
                               "Entrada aleatoria, Timing Alpha y Exposición no pueden usarla; "
                               "el beneficio y la caída de la pestaña Backtest sí la incluyen.",
}

GROUPS = {"nulls": "Modelos nulos", "sweep": "Barrido de ventana",
          "joint": "Nulo conjunto",
          "strata": "Estratos de régimen", "equity": "Cuenta y curvas", "bootstrap": "Bootstrap",
          "exposure": "Exposición", "paired": "Timing Alpha",
          "diagnostics": "Lectura y avisos"}
