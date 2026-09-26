"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "subsets.draws": "Cuántos recortes al azar de la estrategia sin la condición se sortean, "
                  "cada uno con tantas operaciones como la madre.",
    "subsets.seed": "Semilla de esos sorteos, para que dos lecturas coincidan.",
    "verdict.alpha": "Nivel de la prueba: por debajo, la condición mejora la expectativa por "
                     "operación más de lo que lo haría un recorte al azar.",
    "controls.identity_tolerance": "Diferencia relativa de beneficio neto que aún se "
                                   "considera el mismo backtest al comparar la madre "
                                   "reconstruida con lo que guardaba su fichero.",
    "controls.min_paired": "Parte de las operaciones de la madre que la inversión tiene que "
                           "devolver en el mismo instante, con el mismo tamaño y al revés."}
