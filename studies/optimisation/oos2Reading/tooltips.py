"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "null.draws": "Cuántos vectores de signos semanales se sortean; 5.000 es el suelo, con 100.000 "
                  "el error de simulación de la p es de unas milésimas.",
    "null.alpha": "Nivel contra el que se compara la p que se publica; el corte es sólo el signo.",
    "null.seed": "Semilla fija: la misma madre da siempre el mismo resultado.",
    "benchmark.rung": "Qué deja al azar el mono con horas: timing sólo mueve el momento de entrar.",
    "benchmark.draws": "Monos promediados para sacar lo que paga el mercado por la huella de la madre.",
    "benchmark.seed": "Semilla fija de los monos con horas.",
    "max_looks": "Miradas a oos2 que admite una celda; la siguiente se rechaza («solo vivo»)."}
