"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "read.metric": "La métrica cuya correlación decide.",
    "read.companion_metrics": "Métricas en las que se repite la correlación como comprobación.",
    "read.drop_future": "Descarta los tramos cuya ventana acaba después de los datos. Nunca "
                        "false.",
    "measure.min_steps": "Una celda con menos tramos no se correlaciona.",
    "measure.confidence": "Confianza del intervalo del ρ agrupado.",
    "measure.n_resamples": "Remuestreos de ese intervalo.",
    "measure.seed": "Semilla de los remuestreos.",
    "verdict.zero_band": "Cuánto tiene que separarse del cero el intervalo para llamarlo "
                         "predice o perverso.",
    "verdict.drift_high": "Parte de parámetros re-decididos por tramo que cuenta como deriva "
                          "alta."}
