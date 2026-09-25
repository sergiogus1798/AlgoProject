"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "nulls.draws": "Monos por estrategia y por peldaño; el p más pequeño observable es "
                   "1/(monos+1).",
    "nulls.seed": "Semilla de los monos, para que dos lecturas coincidan.",
    "nulls.chunk_trades": "Operaciones valoradas por bloque sembrado. Cambiarlo cambia la "
                          "memoria y también a todos los monos.",
    "nulls.rungs": "Los peldaños de la escalera, de lo más atado a lo más libre.",
    "nulls.headline": "El peldaño cuya p resume: timing cambia sólo el momento de entrar.",
    "barrier.atr_bars": "Periodo del ATR que usan el tamaño por volatilidad y las barreras.",
    "barrier.max_hold": "Barras que se miran hacia delante antes de forzar la barrera "
                        "vertical; una duración real más larga hace que el módulo se niegue.",
    "barrier.intrabar": "Qué barrera gana cuando una vela toca las dos; pessimistic es el stop.",
    "statistics.report": "Los estadísticos que se miden, cada uno con su lado bueno.",
    "verdict.alpha": "Nivel, de una cola, de la p empírica.",
    "verdict.min_trades": "Por debajo de estas operaciones no se calcula p."}
