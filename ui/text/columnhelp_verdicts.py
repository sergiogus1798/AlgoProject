"""The «?» of every study's verdict column: the question it answers and what its words mean.

The words are the ones the window shows: the per-strategy JSON's verdict label when the study
writes one (`ui.daemon.databank.cells.from_json`), else `verdict.csv`'s; a study that only
describes shows «descriptivo» (`ui.daemon.results.store._slim`).
"""

VERDICTS = {
    "gate": "Puerta IS/OOS: una cascada de cribas sobre la población tras su retest fuera de "
            "muestra. MANTENER si pasó todas las cribas duras; DESCARTAR con la primera en que "
            "murió.",
    "isOos": "Qué dicen las métricas IS de los resultados OOS de la población (correlaciones, "
             "persistencia, ranking de predictores). Describe y no juzga estrategias: "
             "«descriptivo».",
    "decay": "¿Cuánto del filo del IS sobrevive fuera de muestra? MANTENER: Sharpe OOS "
             "significativo, la mayoría de sus años ganan y ningún trimestre concentra el "
             "beneficio. DUDOSA: le queda filo, pero no basta. DESCARTAR: no le queda filo, "
             "pierde la mayoría de sus años o debe el beneficio a un trimestre.",
    "snoopingScreen": "¿Bate al buy & hold a igual riesgo una vez pagada la búsqueda entera "
                      "(SPA de Hansen, StepM de Romano y Wolf)? SUPERIOR si el StepM la nombra, "
                      "NO SUPERIOR si no. Anota y no corta: en verdict.csv todas son MANTENER.",
    "crossmarket": "¿Aparece la ventaja en mercados que la estrategia nunca vio? MANTENER si al "
                   "menos en la mitad de sus mercados el intervalo de la esperanza por "
                   "operación (bootstrap 5–95 %, con coste) queda por encima de cero; DESCARTAR "
                   "si no. Es la única criba: los p se enseñan y no deciden.",
    "crossTF": "¿Sobrevive la ventaja leída en un timeframe más lento, con los periodos "
               "escalados? Por timeframe: survives (bate al nulo de cuándo entra allí), "
               "inherited (gana pero no se distingue del azar), fails (no se transfiere), "
               "control_failed (el cambio de parámetros solo ya la rompe en su timeframe), "
               "silent (no operó), unusable (el redondeo movió demasiado los parámetros).",
    "mcRetest": "Si el mundo hubiera sido algo distinto, ¿habrían existido estas operaciones? "
                "SQX re-ejecuta el backtest con una perturbación por tarea y todas a la vez. "
                "STRONG desde 80 de compuesto, ACCEPTABLE desde 65, MARGINAL desde 50; FAIL por "
                "debajo o con un veto; INCONCLUSIVE si un veto de datos impidió juzgar.",
    "spp": "¿Merece esta estrategia miles de variantes? Lee la rejilla de permutación de "
           "parámetros de SQX: SEGUIR si su mejor punto supera el máximo que daría una rejilla "
           "de puro ruido del mismo tamaño efectivo; RUIDO si no.",
    "cloud": "¿Es el punto elegido un pico de suerte o una meseta, y aguanta su nube de "
             "variantes partida por años? Diagnóstico sin veredicto (celda vacía): sus lecturas "
             "están en Punto, Superficie y Temporal.",
    "wfc": "¿Lo que optimiza bien dentro de muestra predice lo que va bien fuera? «fiable» si el "
           "intervalo del 95 % de la ρ entre el Net Profit dentro y fuera de las variantes "
           "queda entero por encima de 0,30; «no fiable» si queda entero por debajo; "
           "«indeciso» si lo cruza: faltan puntos. Cada partición es su subcolumna.",
    "cscv": "¿Elegir parámetros por el mejor resultado dentro de muestra lleva a sobreajuste? "
            "El PBO es en qué parte de las particiones de la historia en dos mitades lo elegido "
            "en una acaba por debajo de la mediana en la otra. «PBO x % con argmax»: pasa hasta "
            "el 50 %, falla por encima.",
    "marketSurfaces": "¿Es la región buena de parámetros la misma en los otros mercados? «la "
                      "región viaja» si en cada tramo leído pasa la parte mínima de los "
                      "mercados declarados; «no viaja» si no la alcanza en ninguno; «a medias» "
                      "si los tramos discrepan.",
    "wfm": "¿Reoptimizar con el Walk Forward Matrix elige lo que luego va mejor? predicts: el "
           "intervalo de la ρ entre el Ret/DD en muestra de lo elegido y el que dio después "
           "queda por encima de 0; blind: cruza el 0 (reoptimizar no aporta); perverse: queda "
           "por debajo (elige lo que va a fallar).",
    "blindJoint": "Paso 20: los cuatro resultados ciegos (WFC, CSCV, superficies, WFM) leídos "
                  "juntos, y si la madre bate al buy & hold en oos2. MANTENER mientras el "
                  "dueño no fije cómo se combinan (anota y no corta); DESCARTAR sólo cuando la "
                  "lectura elegida la tumba.",
    "exposure": "¿Vale el tiempo de mercado que consume? Aprobado si por hora expuesta rinde al "
                "menos 2 veces lo del buy & hold a igual riesgo y se puede leer (30 operaciones, "
                "250 días, ganan los dos); Suspenso si no. Rendir menos que el buy & hold en "
                "total no suspende.",
    "atrCalculator": "¿A qué distancia va un stop fijo X·ATR(20), leído del MAE de las ganadoras "
                     "del IS y sin optimizar? Siempre «N X, sin elegir»: pone cada percentil al "
                     "lado y decide el dueño.",
    "monkey": "¿Es mejor que un mono que opera el mismo mercado? Miles de versiones al azar con "
              "las mismas operaciones, cambiando sólo cuándo entran: «bate al mono» si su "
              "beneficio neto supera al 95 % de ellas (p ≤ 0,05), «no se distingue del mono» si "
              "no.",
    "monteCarlo": "¿De qué depende el resultado: del orden de las operaciones, de cuáles "
                  "ocurrieron, de cómo se llenaron, del régimen? Compuesto de 0 a 100: STRONG "
                  "desde 80, ACCEPTABLE desde 65, MARGINAL desde 50, FAIL por debajo o con un "
                  "veto, INCONCLUSIVE si lo que falla es la muestra. No pregunta si el edge es "
                  "real.",
    "profitShape": "¿De qué pocas cosas está hecho el resultado? Concentración, independencia "
                   "de las operaciones y ruptura de la media, cada una con su lectura en su "
                   "pestaña; sin veredicto global: «descriptivo».",
    "entryQuality": "¿La entrada lleva información o valdría cualquiera? Contra entradas al "
                    "azar a las mismas horas, y entrando una barra tarde; cada lectura en su "
                    "pestaña, sin veredicto global: «descriptivo».",
    "edgeCost": "¿Cuánto edge bruto lleva cada operación sobre lo que cuesta hoy? «por encima "
                "del umbral» si el edge medio llega a 2 veces el coste por operación, «por "
                "debajo» si no. En verdict.csv, DESCARTAR sólo si el dueño eligió eliminar.",
    "conditionalMap": "Dónde, en la rejilla de estados del mercado al entrar, gana la "
                      "estrategia: P&L medio, su intervalo y tasa de acierto por celda. Fabrica "
                      "hipótesis, no filtra: «descriptivo».",
    "structure": "¿Qué condición de entrada lleva el edge, y vive en la dirección? Quita cada "
                 "condición e invierte la estrategia en un lote retesteado por SQX. "
                 "Diagnóstico, nunca selección: «descriptivo».",
    "feedQuality": "¿Cuánto beneficio se apoya en fallos del feed M1 (picos y vuelta, "
                   "congelados, huecos)? «alarma» si las operaciones que tocan uno llevan más "
                   "de lo que daría el azar; «sin alarma» si no; «insuficiente» con menos de 10 "
                   "marcadas. DESCARTAR sólo si el dueño eligió eliminar.",
    "spread": "¿Sigue ganando pagando el spread y el slippage reales de Darwinex en vez del "
              "spread plano de SQX? «cubre el spread real», o «se rompe en IS/OOS» donde un "
              "neto positivo deja de serlo. DESCARTAR sólo si el dueño eligió eliminar.",
}
