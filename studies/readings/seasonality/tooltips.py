"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "shuffle.draws": "Cuántas veces se reparten al azar las mismas operaciones entre las celdas; "
    "más barajadas, p más finas.",
    "shuffle.seed": "Semilla del azar; vacía = una nueva cada corrida (queda guardada), un entero "
    "repite exactamente una corrida.",
    "verdict.min_trades": "Operaciones mínimas de una celda para probarla; por debajo se "
    "enseña como «sin datos suficientes». Decisión del dueño (30).",
    "verdict.fdr_q": "Tasa de falsos descubrimientos (Benjamini-Hochberg) sobre todas las "
    "celdas probadas de una estrategia a la vez.",
}
