"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "scale.window_weeks": "Semanas hacia atrás con las que se mide el movimiento típico de cada "
                          "hora de la semana. Del dueño, en el ledger.",
    "scale.min_weeks": "Semanas de historia que necesita la escala; antes, la vela queda «sin "
                       "escala» y no se detecta nada.",
    "scale.floor_ticks": "Ningún movimiento de menos de estos ticks del feed es «grande», a "
                         "ninguna hora.",
    "scale.floor_rel": "Ni uno por debajo de esta parte de la mediana de las 120 horas de esa "
                       "semana: una hora muerta no marca ruido.",
    "spike.m": "Minutos que tiene un pico para volver.",
    "spike.rho": "Parte del salto que tiene que deshacerse en esos minutos para ser pico-y-vuelta.",
    "spike.m_sensitivity": "Otros m que el informe cuenta al lado, sin efecto en la atribución.",
    "spike.include_non_reverting": "Si los picos que no vuelven marcan también operaciones "
                                   "(decisión 6: no).",
    "rollover_hours": "Horas del reloj del feed que no cuentan ni para congelados ni para "
                      "huecos: el rollover de Nueva York.",
    "frozen.length": "Velas M1 seguidas con OHLC idéntico para llamarlo congelado.",
    "gap.minutes": "Minutos de sesión sin vela para llamarlo hueco.",
    "gap.partial_close_minutes": "Si todos los feeds callan al menos esto, es cierre parcial: "
                                 "se anota y no marca.",
    "gap.max_residual_per_year": "Más huecos propios al año que esto dice que la sesión está "
                                 "mal declarada.",
    "session.share": "Parte de las semanas en que un minuto tiene que tener vela para ser de "
                     "sesión.",
    "session.years": "Años de los que se deduce la sesión de cada feed.",
    "k.candidates": "Valores de K entre los que se elige el de cada feed.",
    "k.quiet_years": "Años tranquilos en los que se cuenta cuántos picos da cada K.",
    "k.max_per_year": "K* es el menor que deja la mediana de esos años por debajo de esto.",
    "stable.base_year": "Desde este año se toma la mediana de huecos que define el año estable.",
    "stable.factor": "Un año es estable si sus huecos no pasan de este múltiplo de la mediana.",
    "stable.b_factor": "Hasta este múltiplo, «calidad B»; por encima, inestable.",
    "stable.floor": "Ningún listón del año estable por debajo de estos huecos al año.",
    "episode.factor": "Un mes es episodio si supera este múltiplo de la mediana de los meses "
                      "anteriores.",
    "episode.months": "Cuántos meses anteriores dan esa mediana.",
    "episode.min_events": "Sucesos mínimos del mes para llamarlo episodio.",
    "alarm.shuffles": "Grupos al azar del test de permutación.",
    "alarm.p_max": "La alarma salta con un p por debajo de esto.",
    "alarm.min_flagged": "Con menos operaciones marcadas, «insuficiente»: no se juzga.",
    "alarm.action": "'mark' sólo marca; 'drop' hace que verdict.csv pida DESCARTAR a la "
                    "estrategia con alarma. Decisión del dueño.",
    "review.extreme_per_column": "Cuántos de los más extremos por columna enseña el informe "
                                 "para revisarlos a mano.",
    "K": "El K de cada feed, medido una vez con el criterio del dueño y congelado en el ledger.",
    "sessions": "La sesión de cada feed, deducida del propio feed y congelada en el ledger."}
