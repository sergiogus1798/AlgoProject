"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "run.sample": "Qué muestra se lee, por su Sample type: OOS1 es el tramo fuera de muestra; "
                  "IST es la ventana que vio el builder.",
    "run.trim": "Cuántas de las mejores operaciones quita la prueba de sensibilidad, una "
                "columna por valor.",
    "run.best_months": "Cuántos de los mejores meses se suman para medir la concentración en "
                       "el calendario.",
    "dependence.lags": "Retardos del Ljung-Box, sobre operaciones y sobre el P&L diario.",
    "dependence.draws": "Barajados detrás de la distribución de la racha perdedora.",
    "dependence.seed": "Semilla de esos barajados, para que dos lecturas coincidan.",
    "breaks.window": "Operaciones por ventana del Sharpe móvil.",
    "breaks.min_trades": "Por debajo de estas operaciones el CUSUM no se lee: el supremo de "
                         "una serie corta es su propio ruido.",
    "verdict.max_top5": "Parte del beneficio total que pueden poner el 5 % de mejores "
                        "operaciones antes de llamarlo concentrado.",
    "verdict.max_best_months": "Parte que pueden poner los mejores meses.",
    "verdict.min_runs_z": "Cuánto de negativo tiene que ser el z de rachas para llamarlo "
                          "agrupamiento.",
    "verdict.alpha": "Nivel de los Ljung-Box y de la racha perdedora."}
