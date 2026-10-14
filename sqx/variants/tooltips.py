"""One sentence per config.yaml knob of the variant factory, for the window's Configuración SQX › WFC."""

TIPS = {
    "size.n_min": "Variantes mínimas por madre (ledger `variants.n_min`). n = min(tope, "
    "máx(mínimo, variantes por coeficiente × p)), con p = 1 + 2k + k(k-1)/2 los "
    "coeficientes de la superficie cuadrática del mapa y k los parámetros vivos.",
    "size.n_max": "Tope de variantes por madre (ledger `variants.n_max`). Si se llega a él, el "
    "lote avisa de que tiene menos variantes por coeficiente que las pedidas.",
    "size.per_coefficient": "Variantes por coeficiente del mapa (ledger `variants.per_coefficient`): "
    "8 es la convención razonable para una cuadrática.",
    "design.seed": "Semilla del hipercubo latino: la misma madre da el mismo lote cada vez. "
    "Se reparte uniformemente sobre la meseta del SPP en build; los congelados y "
    "los shifts quedan en el valor de la madre.",
    "design.frozen.span": "Sólo los pares inertes lo leen: un parámetro congelado se mueve ± "
    "esta fracción de su valor (como hace SQX, ±30 %) y la variante debe "
    "dar lo mismo que la madre. Un shift no se varía nunca.",
    "design.frozen.steps": "Niveles que recorre un parámetro congelado dentro de ese ±.",
    "canaries.n": "Controles cuyo resultado se sabe antes del retest, sacados de los extremos de "
    "la tabla del SPP: una cadena mal cableada devuelve un número mediocre, no el "
    "máximo de la rejilla.",
    "canaries.inert_pairs": "Un par de variantes (estrato `inert`) por parámetro congelado que sólo se diferencian "
    "en él: si dan distinto, el parámetro no estaba muerto.",
    "neighbours.n": "Vecinas que se sortean por madre en el T1 del paso 14. Es un tope: las que "
    "tras redondear salen iguales a la madre o a otra se descartan, no se repiten.",
    "neighbours.entry_pct": "Cuánto se mueve cada parámetro de entrada o de indicador, en ± % de "
    "su valor en la madre. Todos a la vez en cada vecina.",
    "neighbours.exit_pct": "Lo mismo para los parámetros de salida (barras de salida, "
    "coeficientes de stop y de objetivo): ± % de su valor.",
    "neighbours.fixed": "Parámetros que no se mueven nunca, por el final de su nombre: los shifts "
    "y los selectores (método de media, precio aplicado, modo).",
    "neighbours.seed": "Semilla del sorteo; se mezcla con el nombre de la madre, así cada una "
    "tiene sus vecinas y repetir la ejecución da las mismas.",
    "neighbours.int_floor": "Un parámetro entero redondeado nunca baja de este valor: un periodo "
    "de 0 barras no es un periodo.",
    "neighbours.legs": "Tramos en los que se retestean las vecinas, por título de tarea: build y "
    "oos1. Nunca «WFC 3 OOS2»: oos2 está reservado.",
    "neighbours.shape": "Qué miembros lleva cada fichero de vecina. «minimal» pesa 13,7 KB y no "
    "arrastra los resultados de la madre.",
}
