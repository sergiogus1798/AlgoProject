"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "min_trades": "Una combinación que opera menos que esto en alguna de las dos muestras no "
                  "entra en la nube.",
    "rho_floor": "El rho de Spearman que el intervalo entero tiene que superar para llamar "
                 "fiable al ranking.",
    "sharpe_floor": "Sharpe IS mínimo para que una variante entre en el histograma del ratio "
                    "OOS/IS; con un IS cercano a cero el cociente se dispara.",
    "persistence.top": "Persistencia del top: qué parte de las variantes, las mejores del "
                       "build por Net Profit, forman el top. 0.20 es el mejor 20 %.",
    "persistence.keep": "Persistencia del top: en qué parte superior de cada ventana fuera de "
                        "muestra tienen que quedar. 0.50 es la mitad superior, y es también "
                        "lo que saldría por azar.",
    "split_mode": "La composición por defecto: oos2_only (IS build+oos1, OOS oos2) u "
                  "oos1_oos2 (IS build, OOS oos1+oos2); --inside/--outside elige otra."}
