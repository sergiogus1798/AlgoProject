"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "segments": "Qué tramos se leen, una superficie por mercado y tramo. Cada lectura de oos2 "
                "queda apuntada en el ledger.",
    "metric": "La métrica de cada superficie: el beneficio neto por tramo, la misma que lee el "
              "WFC.",
    "min_trades": "Una celda (variante, mercado, tramo) con menos operaciones que esto no "
                  "entra en ese par. Compartido con el WFC y el CSCV.",
    "top_share": "Qué parte de arriba de cada superficie compara el Jaccard y cuenta como "
                 "meseta en el mapa de consenso: 0.10 es el decil.",
    "rho_floor": "El rho que el intervalo entero tiene que superar para decir que dos mercados "
                 "ordenan igual las variantes.",
    "j_quantile": "El percentil del Jaccard de dos órdenes independientes que el observado "
                  "tiene que superar.",
    "min_share": "Qué parte de los mercados declarados tiene que pasar, en cada tramo, para "
                 "decir que la región viaja.",
    "step": "El paso del workflow con el que el ledger apunta esta mirada.",
    "region_radius": "Cuántos escalones de nivel cuenta como vecino de la madre, en todos los "
                     "parámetros a la vez. El mismo número que la nube de parámetros (A1).",
    "region_delta": "Qué tanto por debajo del resultado de la madre en el mercado principal "
                    "sigue contando como parte de la meseta. El mismo número que la nube de "
                    "parámetros (C1).",
    "region_metric": "La segunda métrica que el mapa de calor puede mostrar, sin volver a "
                     "correr el estudio: las dos se calculan siempre."}
