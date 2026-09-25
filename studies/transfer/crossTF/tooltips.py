"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "run.project": "El proyecto por defecto; el comando lo toma del export.",
    "run.feed": "El símbolo de SQX por defecto; --feed lo sustituye y es lo correcto.",
    "run.source_tf": "El timeframe sobre el que se construyeron todas las madres.",
    "run.blocks": "El orden de los <Setup> de la tarea de retest, que es el orden en que "
                  "vuelven los bloques de resultado. Si no coincide, cada celda se valora "
                  "sobre las barras equivocadas y nada falla.",
    "usable.max_rounding_shift": "Cuánto puede mover el redondeo un parámetro escalado antes "
                                 "de que la celda deje de poder atribuirse al timeframe.",
    "usable.reject_clamped": "Descarta las hermanas con algún periodo recortado a su mínimo.",
    "usable.min_trades": "Por debajo de estas operaciones una celda no recibe p.",
    "verdict.statistic": "El estadístico que se compara; sharpe no depende de la escala.",
    "verdict.rung": "El peldaño del nulo que decide: timing aleatoriza sólo el momento de "
                    "entrar.",
    "verdict.alpha": "Nivel de la p.",
    "verdict.control_drop": "Cuánto del estadístico de la madre puede perder el control antes "
                            "de que la celda escalada deje de poder atribuirse al timeframe."}
