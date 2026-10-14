"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "step": "El paso del workflow con el que el ledger apunta esta mirada.",
    "panel.floor_is_per_param": "Operaciones que una variante necesita en el principal (build+oos1) "
    "por cada parámetro vivo. Compartido con el WFC.",
    "panel.floor_oos_per_year": "Operaciones por año de la ventana que una variante necesita en "
    "cada mercado para contar en él. Compartido con el WFC.",
    "panel.min_variants": "Del WFC y el CSCV; este estudio no lo usa (su mínimo es "
    "markets.min_common).",
    "null.draws": "Cuántos sorteos de signos por semana forman el nulo conjunto.",
    "null.block_weeks": "Semanas seguidas que comparten un signo en el volteo.",
    "null.alpha": "Corte de p+ para decir orden positivo y de p− para decir orden perverso.",
    "null.seed": "Semilla raíz: el mismo resultado en cada corrida y con cualquier número de procesos.",
    "null.chunk": "Sorteos que se voltean de una vez; sólo acota la memoria, no cambia el resultado.",
    "null.straddle_max": "Fracción de operaciones cerradas lunes o martes tras un fin de semana a "
    "partir de la cual se avisa y el orden se clasifica también con bloques "
    "de dos semanas.",
    "markets.min_common": "Variantes utilizables a la vez en el principal y en un mercado por "
    "debajo de las cuales ese mercado no entra en la media.",
    "markets.max_ties": "Fracción de variantes empatadas en un mercado por encima de la cual no "
    "entra en la media.",
    "markets.min_weight": "Suma de pesos de los mercados en la media por debajo de la cual el "
    "orden es «sin dato» (un grupo de casi idénticos suma 1).",
    "premium.top_share": "Qué parte de arriba del principal, por exceso neto, forma el top cuya "
    "prima se mide en los otros mercados.",
    "premium.percentile": "Percentil del nulo de la prima en el que, o por debajo del cual, el "
    "paso da LIMBO.",
    "reference.min_rho": "ρ del principal contra sí mismo por encima de la cual se escribe el "
    "cociente ρ conjunta / ρ propia.",
    "power.rhos": "Las correlaciones verdaderas que se plantan para medir qué transmisión es capaz "
    "de ver el paso.",
    "power.draws": "Familias con transmisión plantada por cada correlación de la curva de potencia.",
    "costs.tolerance": "Lo que el P/L reconstruido de una variante puede separarse del NetProfit "
    "de SQX, en moneda de la cuenta.",
    "costs.relative": "Más esta fracción del NetProfit, por las operaciones en los bordes de tramo.",
    "costs.max_share": "Fracción de variantes de un mercado fuera de esa tolerancia a partir de la "
    "cual el estudio avisa.",
    "workers": "Procesos que reconstruyen los mercados en paralelo, uno por mercado.",
}
