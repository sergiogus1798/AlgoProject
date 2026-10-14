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
    "crossmarket": "¿La lógica de la estrategia viaja a otros mercados? El estudio ya no decide: "
    "mide P1-P9 y deja las cifras en las columnas. Quien dice Pasa, Limbo o Falla es "
    "el juez, con las reglas de la zona «Criterios».",
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
    "cloud": "¿Qué parámetros mueven el exceso de la madre, y se puede leer ese ranking? "
    "Diagnóstico sin veredicto (celda vacía): sus lecturas están en R² ajustado, R² "
    "del ruido y Legible.",
    "wfc": "¿Elegir por el pasado sirve fuera? PASA si el top por exceso dentro gana fuera y el "
    "orden no es perverso (un veto levantado, no un voto a favor); LIMBO si gana pero "
    "optimizar empeora, o no hay dato; NO PASA si el top no gana fuera. Se juzga la "
    "composición c1 (build+oos1 → oos2); c2 y c3 se anotan.",
    "cscv": "¿Elegir la mejor variante del pasado sirve fuera? Se corta la historia en 16 bloques "
    "y se prueba cada mitad como «dentro» contra la otra. NO PASA si la elegida pierde "
    "fuera en la mitad de las particiones o más, o si su PBO llega al p95 del nulo; "
    "LIMBO desde el 25 % de pérdida o con pocas variantes; PASA = no descarta.",
    "marketSurfaces": "¿El orden de las variantes en el mercado principal se repite en los demás? "
    "Positivo si lo hace más que el ruido; neutro si no dice nada; perverso "
    "(NO PASA) si va al revés. LIMBO sin dato (menos de 5 mercados con "
    "pesos), con la prima del mejor 20 % bajo el p5 del nulo, o si oos2 sale "
    "perverso.",
    "wfm": "¿Reoptimizar con la Walk Forward Matrix gana en oos2? Sólo cuentan las operaciones "
    "que cierran en oos2, con sus costes. L1 es la mediana de las 30 celdas contra un "
    "nulo de signos semanales: NO PASA si pierde más de lo que explica el ruido (p− ≤ "
    "0,05), LIMBO si no gana, PASA si gana («reoptimizar gana» o «no descarta»).",
    "blindJoint": "Paso 20: los tres resultados ciegos (WFC, CSCV, WFM) leídos "
    "juntos, y si la madre gana en oos2 más que sus mismas operaciones entradas al "
    "azar (operador al azar de igual huella). Provisional: manda el "
    "peor estado. DESCARTAR si alguno es NO PASA, REVISAR si alguno es LIMBO, "
    "MANTENER si todos pasan. Las demás lecturas anotan y no cortan.",
    "exposure": "¿Cuánto tiempo de mercado consume y qué rinde por hora expuesta frente al buy & "
    "hold? Sólo describe: no aprueba ni suspende.",
    "monkey": "¿Es mejor que un mono que opera el mismo mercado? Miles de versiones al azar con "
    "las mismas operaciones, cambiando sólo cuándo entran: «bate al mono» si su "
    "beneficio neto supera al 95 % de ellas (p ≤ 0,05), «no se distingue del mono» si "
    "no.",
    "monteCarlo": "¿De qué depende el resultado: del orden de las operaciones, de cuáles "
    "ocurrieron, de cómo se llenaron, del régimen? Compuesto de 0 a 100: STRONG "
    "desde 80, ACCEPTABLE desde 65, MARGINAL desde 50, FAIL por debajo o con un "
    "veto, INCONCLUSIVE si lo que falla es la muestra. No pregunta si el edge es "
    "real.",
    "entryQuality": "¿La entrada lleva información o valdría cualquiera? Contra entradas al "
    "azar a las mismas horas, y entrando una barra tarde; cada lectura en su "
    "pestaña, sin veredicto global: «descriptivo».",
    "edgeCost": "¿Cuánto edge bruto lleva cada operación sobre el coste que pagó en oos1? «por "
    "encima del umbral» si el edge medio llega a 2 veces ese coste, «por "
    "debajo» si no. En verdict.csv, DESCARTAR sólo si el dueño eligió eliminar.",
    "feedQuality": "¿Cuánto beneficio se apoya en fallos del feed M1 (picos y vuelta, "
    "congelados, huecos)? «alarma» si las operaciones que tocan uno llevan más "
    "de lo que daría el azar; «sin alarma» si no; «insuficiente» con menos de 10 "
    "marcadas. DESCARTAR sólo si el dueño eligió eliminar.",
}
