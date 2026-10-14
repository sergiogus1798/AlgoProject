"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "deciding": "La composición cuyo estado (PASA / LIMBO / NO PASA) es el del paso 17. Las "
    "otras dos se miden y se anotan al lado. build+oos1__oos2 = dentro build y "
    "oos1, fuera oos2.",
    "null.draws": "Cuántas veces se sortean los signos del nulo de volteo. Con 2.000, un p de "
    "0,05 lleva un error de simulación de ±0,5 puntos.",
    "null.block_weeks": "Semanas seguidas de la ventana de fuera que comparten signo en el "
    "nulo. 1 = cada semana se voltea por su cuenta.",
    "null.straddle_warn": "Fracción de operaciones de fuera que cierran en lunes o martes tras "
    "pasar el fin de semana abiertas a partir de la cual se avisa y el "
    "nulo se recalcula con bloques más anchos.",
    "null.alpha": "Corte de p+ y de p−: por debajo, el orden se llama positivo o perverso. "
    "Una familia cuyo orden es puro ruido sale perversa como mucho esta "
    "fracción de las veces.",
    "null.seed": "Semilla del nulo: con la misma, el mismo lote da los mismos p.",
    "order.rho_strong": "ρ de Spearman a partir de la cual un orden positivo se etiqueta "
    "«fuerte» (el 0,30 de Tinsley). Es una etiqueta: no cambia el estado.",
    "level.top_share": "Qué fracción de las variantes, las de mayor exceso dentro, forma el "
    "top que elegiría un optimizador. 0.20 = el mejor 20 %.",
    "level.alpha": "Corte del p del nivel: el top gana fuera sólo si su mediana es mayor "
    "que cero y además supera su nulo de volteo (p del nivel igual o menor "
    "que este corte). Si es mayor que cero sin superarlo, el estado es LIMBO.",
    "level.r_sel_min_gap": "R_sel se escribe «sin dato» si la prima del top dentro no supera "
    "esta fracción del rango intercuartílico del exceso de dentro: "
    "con un denominador casi nulo el cociente no mide nada.",
    "annotate.block_weeks": "Tamaño del bloque, en semanas, con el que se repite el nulo "
    "cuando demasiadas operaciones cierran tras un fin de semana.",
    "check.sqx_tolerance": "Divisa de la cuenta que el neto reconstruido de una variante puede "
    "separarse del NetProfit de SQX sin contar como descuadre.",
    "check.sqx_relative": "Fracción del NetProfit: vale el mayor entre ella y el suelo en divisa, "
    "no su suma.",
    "min_trades": "Suelo del CSCV (paso 18), no del WFC: el paso 17 usa los suelos de "
    "`panel`.",
    "split_mode": "Composición con la que el CSCV lee sus cuatro números cronológicos; el "
    "WFC mide siempre las tres.",
    "panel.floor_is_per_param": "Operaciones mínimas dentro de muestra por parámetro vivo: "
    "con 12 vivos y 15, una variante necesita 180.",
    "panel.floor_oos_per_year": "Operaciones mínimas fuera de muestra por año de la ventana "
    "de fuera.",
    "panel.min_variants": "Con menos variantes que éstas tras los filtros, el paso dice "
    "«sin dato» y queda en LIMBO.",
}
