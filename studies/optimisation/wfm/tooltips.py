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
                          "alta.",
    "benchmark.n_resamples": "Remuestreos del intervalo de la diferencia de Sharpe con el activo.",
    "benchmark.block_days": "Longitud media, en días, de los bloques que se remuestrean juntos.",
    "benchmark.monkey_draws": "Traders al azar con la misma huella contra los que se mide.",
    "benchmark.monkey_min_trades": "Con menos operaciones en el oos2 no se corre el mono.",
    "benchmark.confidence": "Confianza de ese intervalo.",
    "benchmark.seed": "Semilla de esos remuestreos."}
