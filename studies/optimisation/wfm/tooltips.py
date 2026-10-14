"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "modo_real": "Cómo se va a operar en real, fijado antes de correr: fijo (la madre con sus "
    "parámetros) o reoptimizado (se reoptimiza cada cierto tiempo; activa dos "
    "reglas más, que sólo pueden dar LIMBO).",
    "centre.runs": "Número de pasadas de la celda que se operaría en modo reoptimizado.",
    "centre.oos_pct": "% fuera de muestra de esa celda. Se fija antes de mirar oos2.",
    "recharge.charged": "Tramo con cuyos costes se cobró la tarea WFM del export. Las "
    "operaciones que cierran en oos2 se recobran de ése al de oos2.",
    "null.draws": "Sorteos de signos por semana, por madre: los mismos para las 30 celdas.",
    "null.alpha": "Corte de p− (NO PASA) y de p+ («reoptimizar gana»).",
    "null.seed": "Semilla raíz; cada madre recibe una hija por su posición en el export.",
    "null.straddle_max": "Fracción de operaciones cerradas lunes o martes tras un fin de "
    "semana a partir de la cual el nulo se repite en bloques de dos semanas.",
    "null.skew_warn": "Asimetría de la serie semanal de la mediana de celdas a partir de la "
    "cual se avisa de que la cola baja del nulo rechaza de más.",
    "read.drop_future": "Descarta los tramos cuya ventana acaba después de los datos. Nunca "
    "false.",
}
