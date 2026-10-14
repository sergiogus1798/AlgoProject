"""One sentence per config.yaml knob, for the config drawer's hover text."""

TIPS = {
    "travel.draws": "Corridas al azar de «¿la lógica viaja?». Son las mismas para todos los "
    "mercados, ventanas y pruebas; el p más pequeño observable es 1/(draws+1).",
    "travel.seed": "Semilla del sorteo conjunto: se combina con cada año del calendario, así que "
    "una corrida desplaza ese año lo mismo en todos los mercados.",
    "travel.judge_on": "Sobre qué se calculan las z de «¿la lógica viaja?»: gross (bruto, por defecto) "
    "o net (neto). El coste en R depende del ATR de entrada y no se cancela contra "
    "las copias desplazadas; la ventaja por operación (e) siempre va en neto.",
    "travel.shift_unit": "El bloque dentro del que se desplazan las operaciones de una corrida: "
    "year (año natural) o semester. Cada bloque se compara consigo mismo; se "
    "parte donde empieza un tramo del activo principal.",
    "travel.shift_step": "En qué se cuenta el desplazamiento: week conserva el día de la semana y "
    "la hora, que así no puntúan; day conserva sólo la hora.",
    "travel.min_trades_market": "Operaciones mínimas de un mercado: por debajo sigue sumando al "
    "total, pero no cuenta ni a favor ni entre los mercados en contra.",
    "travel.worse_z": "La z de un mercado frente al azar a partir de la cual, hacia abajo, cuenta "
    "como mercado en contra.",
    "travel.frequency": "Control de frecuencia (P2): el |z| de la frecuencia de operaciones que "
    "marca un mercado, y los límites de la sobredispersión estimada en el "
    "build del principal.",
    "travel.validity": "Controles de datos por mercado: cuánto pueden diferir el valor del punto "
    "de la ficha y el de la regresión, y la fracción del ATR mediano por "
    "debajo de la cual una barra se da por defectuosa y se excluye, y la parte "
    "máxima de entradas uniformes que un desplazamiento puede mandar a una "
    "barra posterior por un hueco de datos: por encima, ese mercado y "
    "celda quedan fuera del tensor como sin dato; y el error mediano de precio "
    "(max_fill_error, en múltiplos del ATR mediano) por encima del cual las "
    "velas probablemente no son las del backtest: un spread constante vive "
    "muy por debajo y no lo dispara.",
    "travel.frequency.z": "|z| de la frecuencia de operaciones de un mercado a partir del cual se "
    "marca: opera con una frecuencia distinta a la del principal.",
    "travel.frequency.phi_min": "Límite inferior de la sobredispersión estimada en el build del "
    "principal; por debajo se usa este valor.",
    "travel.frequency.phi_max": "Límite superior de la sobredispersión estimada en el build del "
    "principal; por encima se usa este valor.",
    "travel.validity.point_value_margin": "Diferencia máxima, en proporción, entre el valor del punto "
    "de la ficha y el de la regresión; por encima el mercado "
    "no es válido.",
    "travel.validity.flat_atr_fraction": "Fracción del ATR mediano por debajo de la cual una barra "
    "se da por defectuosa y se excluye.",
    "travel.validity.max_displaced_share": "Parte máxima de entradas uniformes que un desplazamiento "
    "puede mandar a una barra posterior por un hueco de datos; "
    "por encima, ese mercado y celda quedan fuera como sin dato.",
    "travel.validity.max_fill_error": "Error mediano de precio, en múltiplos del ATR mediano, por "
    "encima del cual las velas probablemente no son las del "
    "backtest; un spread constante vive muy por debajo.",
    "travel.degradation.min_trades_year": "Operaciones mínimas de un año; con menos se agrupa con "
    "el siguiente.",
    "travel.degradation.min_years": "Años mínimos tras agrupar; con menos no hay dato de "
    "degradación.",
    "travel.degradation": "Degradación en el tiempo (P9): los años con menos operaciones que el "
    "mínimo se agrupan con el siguiente, y con menos años que el mínimo "
    "tras agrupar no hay dato.",
}

GROUPS = {"travel": "¿La lógica viaja?"}
