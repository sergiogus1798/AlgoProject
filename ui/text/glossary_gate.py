"""The gate's facts and knobs in words (encargo 44): the funnel's rules and the Configuración SQX values."""

# The facts the gate's levels write (encargo 44), as a funnel row reads them: the rule's line
# is «fact + its pass line», the window says the fact in words.
LABELS = {
    "presencia_passed": "Presencia en el retest", "sanidad_passed": "Sanidad y clones",
    "sanidad_value": "Operaciones en OOS1", "estaticas_value": "Neto de OOS1",
    "is_trades_per_year": "Operaciones al año (build)",
    "drift_excess_t": "t del exceso sobre la deriva", "z_frec": "z de la frecuencia",
    "t_b": "t de la degradación en OOS1", "e_fin": "Exceso al final de OOS1",
    "edge_mean_oos": "Ventaja media por operación", "t_exceso_k": "t con el coste estresado",
    "t_sin_mejor_trimestre": "t sin el mejor trimestre", "t_sin_3_mejores": "t sin las 3 mejores",
    "mae_p95_r": "MAE p95 en R", "ret_datos": "Retención con datos alternativos",
    "t_a": "t de la calidad de datos", "n_afectadas": "Operaciones afectadas",
    "retraso_ret_min": "Retención con una barra de retraso",
    "retraso_t_delta": "t de la diferencia con retraso", "q_p": "p de la homogeneidad",
    "dd_p": "p del drawdown", "z_mono": "z del mono", "p_fdr": "Probabilidad de no ser azar",
    # the knobs of the gate's config as the Configuración SQX zone names them (`sqx.` prefix)
    "sqx.on": "Encendida", "sqx.window": "Ventana", "sqx.variant": "Variante del término",
    "sqx.se_skew_kurt": "Error estándar con sesgo y curtosis", "sqx.phi_min": "φ mínima",
    "sqx.phi_max": "φ máxima", "sqx.min_strategies": "Mínimo de estrategias",
    "sqx.cap_log_rate": "Tope del centro (logaritmo)", "sqx.cap_slope": "Tope del centro (pendiente)",
    "sqx.drop_trades": "Operaciones que se quitan", "sqx.drop_period": "Periodo que se quita",
    "sqx.percentile": "Percentil", "sqx.permutations": "Permutaciones", "sqx.block": "Longitud del bloque",
    "sqx.delay.variants": "Retrasos que se prueban",
    "sqx.sequences": "Secuencias", "sqx.on_build": "También sobre el build",
}
