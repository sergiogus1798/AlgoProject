"""The «?» of the study columns of steps 18, 18.5 and 19 (CSCV, market surfaces, WFM), keyed (study, field)."""

STEPS = {
    (
        "cscv",
        "score",
    ): "El PBO de la regla argmax, de 0 a 1 (0,13 es un 13 %); 0,5 es lo que "
    "vale elegir al azar. Los informes recientes lo dejan aquí vacío y lo "
    "dan en el veredicto.",
    (
        "cscv",
        "estado",
    ): "PASA (no descarta), LIMBO o NO PASA. NO PASA si la elegida pierde fuera "
    "en la mitad de las particiones o más, o si el PBO llega al p95 de su "
    "propio nulo; LIMBO desde el 25 % de pérdida o con pocas variantes.",
    (
        "cscv",
        "n",
    ): "Variantes en el panel tras quitar controles, duplicados exactos y las que no "
    "llegan a los suelos de operaciones.",
    (
        "cscv",
        "p_perdida",
    ): "Fracción de las particiones en que la variante elegida dentro "
    "pierde dinero fuera, de 0 a 1. Decide el estado.",
    (
        "cscv",
        "pbo",
    ): "Probabilidad de sobreajuste del backtest: fracción de particiones en que "
    "la elegida dentro queda por debajo de la mediana fuera. 0,5 = elegir no "
    "sirve más que el azar.",
    (
        "cscv",
        "pbo_p",
    ): "Fracción de sorteos del nulo (sin ventaja) con un PBO igual o menor que "
    "el real. Pequeño = el PBO real es más bajo de lo que da el ruido.",
    (
        "cscv",
        "pbo_sobre_p95",
    ): "1 si el PBO real llega al percentil 95 de su propio nulo (peor "
    "que el ruido), 0 si no. Decide el estado.",
    (
        "cscv",
        "orden_estable",
    ): "1 si el PBO queda por debajo del p5 de su nulo tanto en neto "
    "como en bruto: el orden de las variantes resiste los costes.",
    (
        "cscv",
        "beta",
    ): "Pendiente de la recta de degradación: cuánto Sharpe fuera se gana por "
    "cada punto de Sharpe dentro. 1 = se conserva todo; 0 o negativa = elegir "
    "por el pasado no sirve.",
    (
        "cscv",
        "r2",
    ): "R² ajustado de esa recta: qué parte de lo de fuera explica lo de dentro.",
    (
        "cscv",
        "hc",
    ): "Recorte del Sharpe: 1 − mediana fuera ÷ mediana dentro de la elegida. 0,4 "
    "= fuera rinde un 40 % menos. Vacío si dentro no es positiva.",
    (
        "cscv",
        "duplicados_pct",
    ): "Porcentaje de variantes que son copias exactas de otra (mismas "
    "operaciones) y se quitan del panel.",
    (
        "cscv",
        "d01",
    ): "Potencia con un Sharpe anual plantado de 0,1: fracción de sorteos en que "
    "el PBO cae bajo el p5 del nulo. Diagnóstico.",
    ("cscv", "d02"): "Potencia con un Sharpe anual plantado de 0,2. Diagnóstico.",
    ("cscv", "d03"): "Potencia con un Sharpe anual plantado de 0,3. Diagnóstico.",
    (
        "marketSurfaces",
        "call",
    ): "La lectura del estudio, la misma palabra que su veredicto.",
    (
        "marketSurfaces",
        "state",
    ): "pass, watch o fail de esa lectura: PASA, LIMBO o NO PASA.",
    ("marketSurfaces", "estado"): "PASA, LIMBO o NO PASA en palabras del estudio.",
    (
        "marketSurfaces",
        "orden",
    ): "Positivo, neutro, perverso o sin dato: si el orden de las "
    "variantes en el mercado principal se repite en los demás más "
    "de lo que da el ruido (positivo), no dice nada (neutro) o va "
    "al revés (perverso, NO PASA).",
    (
        "marketSurfaces",
        "rho",
    ): "ρ de Spearman media (ponderada) entre el exceso bruto en el "
    "principal y en cada otro mercado, de −1 a +1. Un coeficiente, "
    "no un porcentaje.",
    (
        "marketSurfaces",
        "p_mas",
    ): "Fracción de sorteos del nulo con una ρ igual o mayor que la "
    "observada. Pequeño = el orden viaja más que por ruido.",
    (
        "marketSurfaces",
        "p_menos",
    ): "Fracción de sorteos del nulo con una ρ igual o menor. "
    "Pequeño = lo mejor en el principal es lo peor en los demás.",
    (
        "marketSurfaces",
        "peso",
    ): "Suma de pesos de los mercados que entran en la media: un grupo "
    "de mercados casi idénticos (el trío de EE. UU.) cuenta 1. "
    "Menos de 5 = sin dato.",
    (
        "marketSurfaces",
        "prima",
    ): "Prima del 20 % mejor: cuánto rinde más el top de la madre que "
    "la mediana, neto de costes, en rangos intercuartílicos, "
    "media de los mercados.",
    (
        "marketSurfaces",
        "prima_bajo_p5",
    ): "1 si esa prima cae bajo el p5 de su nulo (el top no "
    "rinde más de lo que da el azar): pasa a LIMBO.",
    (
        "marketSurfaces",
        "rho_auto",
    ): "ρ del principal contra sí mismo (build contra oos1): la "
    "referencia de cuánto orden se repite en el mismo mercado.",
    (
        "marketSurfaces",
        "oos2",
    ): "Verdadero si se leyó también oos2 (el bloque ciego); esa "
    "lectura sólo puede añadir LIMBO.",
    ("marketSurfaces", "segundos"): "Lo que tardó la lectura, en segundos.",
    (
        "marketSurfaces",
        "declared",
    ): "Mercados que _markets.yaml declara para el activo.",
    (
        "marketSurfaces",
        "markets",
    ): "Mercados que entran en la media (con variantes comunes "
    "suficientes y pocos empates).",
    (
        "marketSurfaces",
        "variants",
    ): "Variantes distintas del lote leídas en las superficies.",
    ("wfm", "why"): "Las reglas que dieron ese veredicto.",
    (
        "wfm",
        "modo_real",
    ): "Cómo se va a operar en real, fijado antes de correr: fijo (la madre "
    "con sus parámetros) o reoptimizado (se reoptimiza cada cierto "
    "tiempo; añade dos reglas que sólo pueden dar LIMBO).",
    (
        "wfm",
        "l1_mediana_exceso",
    ): "L1: mediana, entre las 30 celdas, del exceso neto por año "
    "de las operaciones que cierran en oos2. Por encima de 0, "
    "reoptimizar gana fuera.",
    (
        "wfm",
        "l1_p_mas",
    ): "Fracción de sorteos del nulo de signos semanales con una mediana "
    "igual o mayor. Pequeño = «reoptimizar gana».",
    (
        "wfm",
        "l1_p_menos",
    ): "Fracción de sorteos del nulo con una mediana igual o menor. Pequeño "
    "(≤ 0,05) = pierde más de lo que explica el ruido: NO PASA.",
    (
        "wfm",
        "l2_delta",
    ): "L2: exceso de la celda cruzada menos el de la referencia (la serie "
    "semanal mediana de las celdas). Se anota; no decide.",
    (
        "wfm",
        "l2_p_menos",
    ): "Fracción de sorteos del nulo con un delta igual o menor. Sólo "
    "cuenta en modo reoptimizado.",
    ("wfm", "centro_exceso_oos2"): "Exceso por año en oos2 de la celda que se operaría "
    "(elegida antes de mirar). Sólo cuenta en modo reoptimizado.",
    (
        "wfm",
        "celdas_efectivas",
    ): "Cuántas curvas independientes valen las 30 celdas (de sus "
    "correlaciones). Suele ser 1-4: no son 30 pruebas.",
    (
        "wfm",
        "frac_celdas_positivas",
    ): "Fracción de las 30 celdas con exceso positivo en oos2.",
    (
        "wfm",
        "deriva",
    ): "Cuánto cambian los parámetros elegidos entre una reoptimización y la "
    "siguiente, de 0 a 1. Se anota.",
    (
        "wfm",
        "area_celdas",
    ): "Celdas que pasan la regla de área de SQX con la nota recalculada "
    "sólo en oos2. Se anota; no decide.",
    (
        "wfm",
        "area_pasa",
    ): "Verdadero si esa regla de área de SQX pasa con la nota de oos2.",
    (
        "wfm",
        "asimetria",
    ): "Asimetría de la serie semanal mediana de celdas. Alta = la cola "
    "baja del nulo rechaza de más (aviso).",
    (
        "wfm",
        "recobro_oos2",
    ): "Dinero que se cobra de más a las operaciones de oos2 para llevar "
    "los costes del export a los de oos2.",
    (
        "wfm",
        "sqx_failed",
    ): "Verdadero si la regla de área de SQX marcó la madre (una marca, "
    "nunca un juez).",
}
