"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "run.symbol": "El activo cuya política dice dónde empieza cada tramo.",
    "run.metric": "La métrica con la que se lee la nube.",
    "run.min_trades": "Una variante que opera menos que esto no es un punto de la superficie.",
    "run.exclude_strata": "Estratos del diseño que se dejan fuera: los canarios están en los "
                          "extremos a propósito.",
    "neighbourhood.radius": "Cuántos pasos de rejilla cuentan como vecindad del punto elegido.",
    "neighbourhood.delta": "Cuánto por debajo sigue contando como compañía, para π(δ).",
    "surrogate.neighbours": "Vecinos más cercanos contra los que se mide la rugosidad sin "
                            "modelo.",
    "surrogate.sobol_power": "2 elevado a esto puntos base para los índices de Sobol; es "
                             "aritmética, no backtests.",
    "surrogate.seed": "Semilla de los índices de Sobol.",
    "stability.period": "El periodo de la lectura temporal: YE años, 2QE semestres.",
    "stability.min_active_days": "Días activos que necesita un periodo para leerse.",
    "stability.top_share": "La parte de mejores clones cuyo centroide se sigue.",
    "ensemble.k": "Miembros de la meseta en la mezcla de diagnóstico.",
    "verdict.rank_high": "Por encima de este rango el origen es de lo mejor de su vecindad.",
    "verdict.plateau_low": "Por debajo de esta compañía está solo: es un pico.",
    "verdict.roughness_high": "1 − r² del modelo suave por encima del cual es rugosa.",
    "verdict.local_roughness_high": "Desacuerdo entre vecinos, en IQR, por encima del cual es "
                                    "rugosa.",
    "verdict.slope_high": "Pendiente en el origen por encima de la cual el óptimo está en otro "
                          "sitio.",
    "verdict.rho_low": "Spearman mediano entre periodos por debajo del cual se rebaraja.",
    "verdict.drift_high": "Movimiento mediano del centroide por encima del cual la región "
                          "buena se desplaza.",
    "verdict.fraction_low": "Por debajo de esta parte de clones ganadores, un periodo "
                            "sostiene a los demás."}
