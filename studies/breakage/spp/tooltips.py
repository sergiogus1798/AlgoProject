"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "design.min_span": "Los niveles cubren como mínimo ± esta fracción del valor original: 0.30 "
                       "es ±30 %.",
    "read.metric": "La métrica sobre la que se decide: el ruido, la influencia y las mesetas.",
    "read.companion_metrics": "Métricas que se leen al lado sólo para la tabla de η².",
    "read.breakeven": "Dónde la métrica deja de ser rentable: 1.0 para profit factor, 0 para "
                      "el resto.",
    "verdict.margin": "Cuántas veces tiene que superar el máximo observado al máximo de una "
                      "rejilla de ruido.",
    "design.n_target": "Variantes para las que se dimensiona el diseño.",
    "design.strata": "Qué parte de las variantes va a la vecindad, al factorial y a la "
                     "cobertura.",
    "design.min_levels": "Niveles mínimos de un parámetro vivo.",
    "design.max_levels": "Niveles máximos, explique la varianza que explique.",
    "design.plateau_share": "Cuánto por debajo del mejor nivel sigue contando como meseta.",
    "surface.top_share": "Qué parte de arriba de cada superficie de dos parámetros es meseta: "
                         "0.10 es el decil superior de sus celdas."}
