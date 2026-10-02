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
    "design.n_target": "Tope de variantes por madre: el diseño se dimensiona para este número "
                       "y nunca repite una combinación para llegar a él; si el espacio es más "
                       "pequeño, se fabrica entero.",
    "design.strata": "Qué parte de las variantes va a la vecindad, al factorial y a la "
                     "cobertura.",
    "design.min_levels": "Niveles mínimos de un parámetro vivo.",
    "design.max_levels": "Niveles máximos, explique la varianza que explique.",
    "design.plateau_share": "Cuánto por debajo del mejor nivel sigue contando como meseta.",
    "panel1.band_share": "Ancho de la banda de cada histograma: mediana ± este porcentaje de "
                         "su propio valor. 0.30 es ±30 %."}
