"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "run.timeframes": "Los marcos temporales que se agrupan.",
    "run.workers": "Procesos en paralelo, un activo y marco cada uno.",
    "run.budget_bytes": "Memoria máxima, en bytes, que el juicio puede ocupar con los sorteos "
    "de un grupo.",
    "run.seed": "Semilla; vacía, se sortea una y se guarda para que una reanudación remuestree "
    "igual.",
    "groups.by": "Cómo se agrupan los activos: por la clase de la memoria de resultados.",
    "groups.min_assets": "Activos con operaciones suficientes que necesita una prueba de grupo.",
    "judge.alpha": "Tasa de falsos descubrimientos que se tolera entre todas las pruebas de "
    "grupo.",
    "judge.clock": "Si se incluyen las medidas de reloj; nunca llegan al tablero.",
    "judge.placebos": "Sorteos de la nula que se juzgan como si fueran la serie real, para "
    "contar las falsas alarmas.",
}
