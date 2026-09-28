"""One sentence per config.yaml knob of the IS/OOS study, for the window's configuration drawer."""

TIPS = {
    "trades.bins": "Cuántas barras tiene cada histograma. IS y OOS comparten las mismas, para "
                   "que una barra signifique lo mismo en las dos muestras.",
    "trades.tail_pct": "Qué porcentaje de cada cola queda fuera del eje: las operaciones más "
                       "extremas se suman a la primera o la última barra en vez de estirar el "
                       "gráfico hasta que todo lo demás sea una raya.",
}
