"""The words step 17 is read with: labels, the sentence of each cell of the table, column help."""

LABEL = {"pasa": "PASA", "limbo": "LIMBO", "no_pasa": "NO PASA"}
STATE = {"pasa": "pass", "limbo": "watch", "no_pasa": "fail"}
ORDER = {
    "positivo": "Positivo",
    "neutro": "Neutro",
    "perverso": "Perverso",
    "sin_dato": "Sin dato",
}

# (order, the top wins outside) -> the cell of the owner's table (proposal, section 6).
MEANING = {
    (
        "positivo",
        True,
    ): "Elegir sirve y lo elegido gana: el orden de dentro se repite fuera más "
    "de lo que daría el ruido, y el top que elegiría un optimizador gana fuera.",
    (
        "neutro",
        True,
    ): "Meseta plana: el orden de dentro no dice nada fuera, pero el top gana "
    "fuera. Los parámetros dan igual y la idea gana.",
    (
        "perverso",
        True,
    ): "El top gana fuera, pero lo mejor de dentro tiende a ser lo peor de "
    "fuera: optimizar empeora. En real habría que operar el centro de la "
    "meseta, no el óptimo.",
    (
        "positivo",
        False,
    ): "El orden se mantiene, pero el top no gana fuera: ningún orden salva a "
    "una familia cuyo top pierde.",
    (
        "neutro",
        False,
    ): "El top que elegiría un optimizador no gana fuera, y el orden de dentro "
    "no dice nada.",
    (
        "perverso",
        False,
    ): "El top no gana fuera y, además, lo mejor de dentro tiende a ser lo "
    "peor de fuera.",
}
NOT_BEATEN = (
    " Pero la mediana del top, aunque mayor que cero, no supera su nulo de volteo "
    "(p del nivel {p} > {alpha}): no se distingue del ruido y el estado es LIMBO."
)
VETO = (
    " Un PASA levanta un veto: dice que, dentro de esta familia, elegir por el pasado no "
    "lleva a algo que pierda fuera; no dice que la madre tenga ventaja."
)
NO_DATA = (
    "Sin dato: quedan menos de {need} variantes tras los filtros, o la madre no tiene "
    "operaciones en la ventana de fuera. No hay nada que juzgar."
)

COLUMNS = [
    "Composición",
    "Dentro",
    "Fuera",
    "Variantes",
    "ρ de Spearman",
    "p+",
    "p−",
    "Nulo p5",
    "Nulo p95",
    "Orden",
    "Variantes en el top",
    "Nivel del top",
    "p del nivel",
    "Nivel de todas",
    "R_sel",
    "Estado",
]
NUMBERS = [
    "ρ de Spearman",
    "p+",
    "p−",
    "Nulo p5",
    "Nulo p95",
    "Variantes en el top",
    "Nivel del top",
    "p del nivel",
    "Nivel de todas",
    "R_sel",
]
HELP = [
    "c1 decide; c2 y c3 se anotan. Las tres leen oos2: que coincidan no es una confirmación.",
    "Los tramos que cuentan como dentro de muestra: lo que un optimizador ya habría visto.",
    "Los tramos que cuentan como fuera de muestra.",
    "Variantes medidas, tras quitar controles, duplicados exactos y las que no llegan a los "
    "suelos de operaciones.",
    "Correlación de rangos entre el exceso por año de dentro y el de fuera, variante a "
    "variante, ANTES de costes (las variantes que operan más pagan más dentro y fuera, y eso "
    "solo ya las ordenaría igual en los dos lados). Va de −1 a +1: +1 es el mismo orden dentro y fuera, 0 ningún parecido, −1 el "
    "orden invertido. Es un coeficiente, no un porcentaje.",
    "Fracción de sorteos del nulo con una ρ igual o mayor que la observada. Pequeño (≤ α) = "
    "el orden de dentro se repite fuera más de lo que daría el ruido: orden positivo.",
    "Fracción de sorteos del nulo con una ρ igual o menor que la observada. Pequeño (≤ α) = "
    "lo mejor de dentro tiende a ser lo peor de fuera: orden perverso.",
    "Percentil 5 de la ρ en el nulo: la misma familia sin ventaja fuera. A cada semana de fuera "
    "se le sortea un signo, el mismo para todas las variantes, así siguen pareciéndose entre "
    "sí igual que antes y cada una espera cero.",
    "Percentil 95 de la ρ en ese mismo nulo. Una ρ observada entre el p5 y el p95 no se "
    "distingue del ruido.",
    "Positivo, neutro o perverso según p+ y p−. «Fuerte» es un orden positivo con ρ igual o "
    "mayor que el 0,30 de Tinsley: una etiqueta, no cambia el estado.",
    "Cuántas variantes forman el top: las de exceso de dentro igual o mayor que el percentil "
    "que deja arriba la fracción configurada (con empates pueden ser algunas más).",
    "Mediana del exceso por año FUERA de las variantes del top de dentro, después de costes, "
    "en la divisa de la cuenta. Por encima de cero, lo que elegiría un optimizador gana fuera.",
    "Fracción de sorteos del nulo de volteo (los mismos del orden) cuya mediana del top es "
    "igual o mayor que la observada. Pequeño = el top gana fuera más de lo que daría el "
    "ruido. PASA exige que sea igual o menor que el alfa del nivel.",
    "Mediana del exceso por año fuera de todas las variantes medidas.",
    "Retención de la prima de selección: (nivel del top − nivel de todas) fuera, dividido "
    "por lo mismo dentro. 1 = la ventaja del top se conserva entera; 0 = elegir no sirve; "
    "negativo = selección perversa. Vacío cuando la prima de dentro es casi nula.",
    "PASA, LIMBO o NO PASA, sólo en la composición que decide.",
]
TABLE_NOTE = (
    "El exceso es el del paso 14: el beneficio de cada operación menos lo que el "
    "mercado pagó por estar dentro, sumado por variante y dividido por los años de "
    "la ventana. El orden (ρ, sus p y su nulo) se mide antes de costes; el nivel y "
    "R_sel, después de costes, que es dinero. Decide sólo c1; cada composición lleva "
    "su propio nulo."
)

CLOUD_HELP = (
    "Un punto por variante: en horizontal su exceso por año dentro, en vertical "
    "fuera, los dos después de costes. Los cuadrantes dicen lo que la ρ no ve: una nube inclinada puede estar "
    "entera en el cuadrante que gana dentro y pierde fuera."
)
CLOUD_NOTE = (
    "La recta es la de la ρ de Spearman, no un ajuste de mínimos cuadrados: pasa por "
    "las dos medianas con pendiente ρ × (rango intercuartílico de fuera ÷ el de "
    "dentro). La ρ de la recta es la del orden, medida antes de costes; los puntos y los "
    "cuadrantes son después de costes."
)

# fact -> column, in the order of the annotated table.
ANNOTATED = {
    "fines_de_semana": "Cierres tras fin de semana",
    "p_mas_bloque": "p+ por bloques",
    "p_menos_bloque": "p− por bloques",
    "orden_bloque": "Orden por bloques",
    "r_sel_p5": "R_sel nulo p5",
    "r_sel_p95": "R_sel nulo p95",
    "nivel_top_deriva_previa": "Nivel del top, deriva previa",
    "rho_parcial": "ρ parcial",
    "descuadre_sqx": "Descuadre con SQX",
    "rho_sin_suelos": "ρ sin suelos",
    "n_sin_suelos": "Variantes sin suelos",
    "cuadrante_pp": "++",
    "cuadrante_pn": "+−",
    "cuadrante_np": "−+",
    "cuadrante_nn": "−−",
}
ANNOTATED_HELP = [
    "Fracción de las operaciones de fuera que cierran en lunes o martes tras pasar el fin de "
    "semana abiertas. Dos variantes casi iguales que cierran la misma operación una el viernes "
    "y otra el lunes caen en semanas distintas, y el nulo las trata como menos parecidas de lo "
    "que son.",
    "p+ con el nulo sorteado por bloques de varias semanas. Sólo se calcula cuando los cierres "
    "tras fin de semana pasan del aviso.",
    "p− con el nulo por bloques.",
    "El orden que saldría con el nulo por bloques: si no coincide con el de arriba, la "
    "clasificación depende de cómo se parten las semanas. No decide.",
    "Percentil 5 de R_sel en el nulo de volteo.",
    "Percentil 95 de R_sel en el nulo de volteo: un R_sel dentro del rango no se distingue "
    "de no retener nada.",
    "El nivel del top con la deriva medida sólo en barras anteriores a oos2 (build y oos1), "
    "la que se podía conocer antes de operar ese tramo. Sólo donde fuera es oos2.",
    "ρ de Spearman entre el exceso de dentro y el de fuera quitando de ambos lo que explican "
    "las operaciones de dentro y las de fuera: si baja mucho respecto a la ρ, las variantes "
    "coinciden sobre todo porque operan más o menos, no por su exceso. Anotación: no decide.",
    "Fracción de variantes cuyo beneficio neto reconstruido se separa del NetProfit de SQX "
    "más de la tolerancia, en el peor tramo. Es la comprobación de los costes: 0 = cuadra.",
    "La ρ de la composición que decide sin los dos suelos de operaciones: las variantes que "
    "operan poco no son una muestra al azar, son una zona del espacio.",
    "Cuántas variantes entran en esa ρ sin suelos.",
    "Variantes que ganan dentro y fuera.",
    "Ganan dentro y pierden fuera.",
    "Pierden dentro y ganan fuera.",
    "Pierden dentro y fuera.",
]
ANNOTATED_NOTE = (
    "Nada de esta tabla decide. Los bloques del volteo son de {weeks} semanas "
    "seguidas de la ventana de fuera."
)

# count of `engines.variants.filters.screen` -> row, in the order the filters act.
FILTERS = {
    "lote": "Variantes del lote",
    "controles": "− controles (canarios y pares inertes)",
    "suelo_dentro": "− bajo el suelo de dentro (operaciones por parámetro vivo)",
    "duplicados": "− duplicados exactos",
    "suelo_fuera": "− bajo el suelo de fuera (operaciones por año)",
    "sin_valor": "− sin operaciones exportadas",
    "quedan": "Quedan",
    "vivos": "Parámetros vivos (k)",
}
FILTERS_NOTE = (
    "Un suelo que la propia madre no cumple no se aplica y se avisa arriba. Un "
    "duplicado exacto es la misma lista de operaciones en los tramos leídos."
)

TAB_NOTE = (
    "Si ordeno las variantes de la madre por lo que ganaron dentro de muestra, ¿ese "
    "orden se parece al de fuera? Y lo que elegiría un optimizador, ¿gana fuera? La "
    "primera pregunta la contesta la ρ de Spearman contra su nulo; la segunda, el "
    "nivel del top."
)
GLOSSARY = [
    {
        "term": "exceso",
        "text": "El beneficio de una operación menos la deriva: lo que el "
        "mercado pagó por estar dentro durante las barras que duró. Es el del paso 14.",
    },
    {
        "term": "nulo de volteo",
        "text": "La misma familia sin ventaja fuera de muestra: el "
        "exceso de cada semana de fuera (cada operación entera en la semana en que cierra) se "
        "multiplica por +1 o −1 al azar, el mismo signo para todas las variantes. Conserva cuánto se parecen las variantes entre sí, que es lo que el "
        "intervalo de Fisher ignoraba.",
    },
    {
        "term": "PASA / LIMBO / NO PASA",
        "text": "PASA: el top gana fuera (la mediana de su "
        "exceso neto es mayor que cero y supera su nulo de volteo: p del nivel ≤ alfa del "
        "nivel) y el orden no es perverso. LIMBO: la mediana es mayor que cero pero no supera "
        "el nulo, o gana y optimizar empeora (orden perverso), o no hay dato. NO PASA: la "
        "mediana del top es cero o menor, diga lo que diga el orden.",
    },
    {
        "term": "antes y después de costes",
        "text": "El exceso bruto suma a cada operación la "
        "comisión, el swap, el spread y el deslizamiento que se le cobraron (los de la ficha del "
        "activo). El orden se mide en bruto; el nivel, en neto.",
    },
]
