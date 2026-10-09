"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "run.cells": "Las celdas (activo/marco) donde se planta el edge.",
    "run.workers": "Procesos en paralelo, una réplica cada uno.",
    "run.budget_bytes": "Memoria máxima, en bytes, que puede ocupar el estudio; se recortan "
                        "los procesos para caber.",
    "run.process_bytes": "Memoria que ocupa un proceso, en bytes (medida).",
    "run.seed": "Semilla; vacía, se sortea una nueva y se apunta en run.json.",
    "plant.how": "Dónde se planta: en las barras que siguen a la condición de la medida, o en "
                 "barras al azar con la misma frecuencia (el control).",
    "plant.effects": "Tamaños del edge plantado: ganancia media bruta por operación, en "
                     "múltiplos del coste de ida y vuelta.",
    "plant.replications": "Copias de cada celda con el signo de cada barra al azar: la misma "
                          "volatilidad real y ninguna dirección.",
    "plant.directions": "Direcciones en las que se planta; la base no tiene dirección, así que "
                        "corto es el espejo de largo.",
    "plant.measures": "La medida que lleva el edge plantado de cada familia.",
    "judge.cut": "La p que una prueba tiene que alcanzar; vacía, la que impone hoy la corrección "
                 "del mapa entero.",
    "judge.chunk": "Sorteos de la nula por tanda; una réplica para en cuanto el corte ya es "
                   "inalcanzable.",
    "judge.single_level": "Nivel de la prueba sin corregir, como si la regla fuera la única.",
    "judge.power": "Tasa de detección a la que se lee el efecto mínimo detectable.",
}
