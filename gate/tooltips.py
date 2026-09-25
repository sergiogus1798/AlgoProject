"""One sentence per config.yaml knob, for the window's configuration drawer.

A screen's knob is addressed by the screen's own name, as `--set` takes it."""

TIPS = {
    "sanidad.min_trades": "Operaciones mínimas en la cosecha para que la estrategia se lea.",
    "estaticas.keep": "La condición sobre las métricas fuera de muestra que tiene que cumplir, "
                      "escrita como la lee la criba.",
    "estaticas.value": "La métrica que se enseña como número de esta criba.",
    "degradacion.min_retention": "Qué parte del filo dentro de muestra tiene que sobrevivir "
                                 "fuera.",
    "degradacion.min_t": "Cuántos errores estándar tiene que batir lo que queda.",
    "degradacion.min_years_positive": "Años fuera de muestra con beneficio positivo, como "
                                      "mínimo.",
    "degradacion.max_concentration": "Parte del beneficio fuera de muestra que puede poner "
                                     "un solo año.",
    "forma.max_dd_ratio": "Cuántas veces puede ser el peor descenso fuera de muestra el "
                          "esperado; 5 es casi no pedir nada.",
    "mono.statistic": "El estadístico con el que la estrategia se mide contra sus monos.",
    "mono.rung": "El peldaño del nulo; timing sólo aleatoriza el momento de entrar.",
    "mono.max_p": "La p más alta que se deja pasar; laxa a propósito.",
    "familia.alpha": "Nivel de la corrección por multiplicidad sobre todas las p del mono. "
                     "Blanda: informa, no elimina.",
    "monkey.draws": "Corridas nulas por estrategia; el resto de mandos del nulo son los de "
                    "engines/nulls/config.yaml.",
    "monkey.timeframe": "Las barras sobre las que se colocan los monos."}
