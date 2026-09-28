"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "min_trades": "Una combinación que opera menos que esto en alguna de las dos muestras no "
                  "entra en la nube.",
    "rho_floor": "El rho de Spearman que el intervalo entero tiene que superar para llamar "
                 "fiable al ranking.",
    "split_mode": "La composición por defecto: oos2_only (IS build+oos1, OOS oos2) u "
                  "oos1_oos2 (IS build, OOS oos1+oos2); --inside/--outside elige otra.",
    "table_ends": "Cuántas combinaciones de cada extremo del ranking enseña la tabla."}
