"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "run.project": "El proyecto por defecto; el comando lo toma del export.",
    "run.blocks": "El orden de los <Setup> de la tarea de retest, que es el orden en que "
                  "vuelven los bloques de resultado. Vacío, se deduce del timeframe de las "
                  "madres y de assets/_build.yaml; una lista sólo si la tarea se escribió con "
                  "--timeframes. Si no coincide, cada celda se valora sobre las barras "
                  "equivocadas y nada falla.",
    "run.seed": "La semilla de los nulos de timing. Vacía, una nueva en cada corrida (queda "
                "apuntada en el manifest); un número repite la corrida exacta.",
    "usable.min_trades": "Por debajo de estas operaciones una celda no recibe p.",
    "verdict.statistic": "El estadístico que se compara; sharpe no depende de la escala.",
    "verdict.rung": "El peldaño del nulo que decide: timing aleatoriza sólo el momento de "
                    "entrar.",
    "verdict.alpha": "Nivel de la p de la celda y, como cuantil normal, de z_new.",
    "tf.neighbours": "Por temporalidad de la madre, las dos hermanas vecinas que deciden si la "
                     "ventaja tiene un pico aislado.",
    "tf.far": "La hermana lejana de cada temporalidad de madre: se anota y, si falla la "
              "retención, baja un Pasa a Limbo. Nunca decide sola.",
    "tf.runs": "Las corridas al azar conjuntas: cuántas (draws), su semilla, si las z se leen "
               "sobre el bruto o el neto (judge_on), el bloque que se desplaza (un año) y en "
               "qué se cuenta el desplazamiento (semanas), y los dos controles de huecos en "
               "los datos. La madre y todas sus hermanas se desplazan igual en cada corrida.",
    "tf.comparable": "Cuándo una hermana deja de ser comparable con su madre: el redondeo "
                     "relativo máximo de un periodo y las operaciones mínimas en la ventana "
                     "que se mide. Una no comparable no entra en ningún test.",
    "tf.frequency": "Frecuencia (T1): el |z| hasta el que Pasa y a partir del que No pasa, "
                    "los límites de la sobredispersión de los recuentos anuales de la madre y "
                    "el mínimo de hermanas comparables de la corrida para que haya población.",
    "tf.retention": "Retención en oos1 (T2a): la fracción de la ventaja de la madre que la "
                    "hermana debe conservar para Pasar, la z de la diferencia que hace falta "
                    "para No pasar cuando no conserva nada, y la retención por debajo de la "
                    "cual la otra vecina confirma el pico aislado.",
    "tf.build": "La hermana frente al azar en el build (T2b): la z a partir de la cual Pasa y "
                "la z hasta la cual No pasa."}
