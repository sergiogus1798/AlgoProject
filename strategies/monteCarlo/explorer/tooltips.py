"""One sentence per config.yaml and asset knob, for the config drawer's hover text."""

TIPS = {
    "global.starting_equity": "Cuenta desde la que arranca la curva de equity aditiva.",
    "global.risk_per_trade": "USD arriesgados por operación; el divisor que convierte el "
                             "P&L en R.",
    "global.n_sims": "Rutas simuladas por cada sub-prueba.",
    "global.chunk": "Rutas por lote de cada worker; es memoria, no estadística.",
    "global.max_workers": "Núcleos usados en paralelo. Vacío (null) = todos los que tenga "
                          "esta máquina. Pedir más de los que tienes no falla ni acelera: "
                          "no puede haber más paralelismo real que núcleos, y sobran "
                          "procesos compitiendo por los mismos — puede incluso ir más lento.",
    "global.percentile_set": "Percentiles que se guardan de cada distribución.",
    "global.report_percentile": "El percentil contra el que se compara el valor observado, "
                                "y el que marcan todos los histogramas.",
    "global.progress_update_pct": "Cada cuánto se refresca la barra de progreso, en %.",
    "blocks.block_min": "Bloque más pequeño de operaciones consecutivas que se mantiene "
                        "junto.",
    "blocks.min_blocks": "Un reordenamiento necesita al menos estos bloques para "
                         "aleatorizar algo.",
    "blocks.n_block_sizes": "Tamaños de bloque, repartidos uniformemente entre block_min y "
                            "N / min_blocks.",
    "family_b.oos_amber_frac": "Sharpe mediano OOS por debajo de esta fracción del de IS: "
                              "aviso.",
    "family_b.oos_red_frac": "Sharpe mediano OOS por debajo de esta fracción del de IS: "
                            "veto.",
    "family_b.outlier_frac": "Beneficio neto perdido al quitar la mejor operación, a partir "
                             "del cual se avisa.",
    "family_c.p_skip": "Probabilidad de que cada operación se pierda al azar.",
    "family_c.skip_keep_frac": "Beneficio mínimo que debe sobrevivir a las entradas "
                               "perdidas.",
    "family_c.cost_shock_range": "Rango del que se sortea el multiplicador de comisión y "
                                 "swap.",
    "family_c.fill_frac": "Probabilidad de que cada operación sufra una ejecución "
                          "degradada.",
    "family_c.fill_depth": "Fracción máxima de la distancia P&L–MAE que devuelve una "
                           "ejecución degradada.",
    "family_c.fill_keep_frac": "Beneficio mínimo que debe sobrevivir a las ejecuciones "
                               "degradadas.",
    "family_c.spread_scale": "Rango del que se sortea el multiplicador del spread.",
    "family_c.cost_crosscheck": "Si se compara la comisión modelada contra la que SQX "
                                "cobró de verdad.",
    "family_d.window_months": "Duración de cada ventana móvil o bloque no solapado, en "
                              "meses.",
    "family_d.window_step_months": "Meses entre el inicio de una ventana móvil y la "
                                   "siguiente.",
    "family_d.window_pass_frac": "Fracción de ventanas que deben quedar en positivo en su "
                                 "percentil 5.",
    "family_d.window_sims": "Rutas de bootstrap dentro de una ventana o un tercil de "
                            "régimen.",
    "family_d.vol_model": "atr o garch — qué modelo de volatilidad define el régimen.",
    "family_d.atr_period": "Periodo del ATR, en días.",
    "family_d.garch_order": "Orden (p, q) del GARCH.",
    "family_d.garch_dist": "Distribución de los residuos del GARCH (p. ej. t).",
    "family_d.regime_concentration": "Fracción del beneficio en un solo tercil de "
                                     "volatilidad que dispara un aviso.",
    "family_e.psr_benchmark": "Sharpe contra el que se prueba la PSR (0 = cualquier edge).",
    "family_e.psr_gate": "PSR por debajo de esto veta el veredicto.",
    "family_e.psr_target": "PSR por debajo de esto (pero por encima del veto) es aviso.",
    "scoring.dd_inflation_flag": "Ratio drawdown reordenado / backtest por encima del cual "
                                 "veta.",
    "scoring.dd_inflation_watch": "Ratio drawdown reordenado / backtest por encima del cual "
                                  "avisa.",
    "scoring.survival_dd_pct": "Techo de drawdown como fracción de la cuenta — "
                               "provisional hasta saber la regla real de la prop firm.",
    "scoring.min_pf": "Profit factor mínimo en las comprobaciones de percentil 5.",
    "scoring.weights": "Peso de cada familia en el compuesto.",
    "scoring.tiers": "Cortes del compuesto para PASS / WATCH / WEAK.",
    "stability.n_stability_runs": "Repeticiones independientes para medir cuánto se mueven "
                                  "los números que deciden.",
    "stability.stability_tol": "Dispersión relativa entre repeticiones por encima de la "
                               "cual conviene subir n_sims.",
    "point_value": "USD por 1.0 de precio por 1.0 lote.",
    "tick_size": "Incremento de precio más pequeño.",
    "spread": "Spread que asumió SQX, en puntos.",
    "commission": "Comisión que cobró SQX, USD por lote y lado.",
}
