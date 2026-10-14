"""The facts and knobs of steps 17-19 (WFC, CSCV, market surfaces, WFM) in words, as the Criterios zone and the drawers read them."""

# Bare keys are facts (the last part of `cscv.p_perdida`); `knob.` keys are config.yaml knobs.
# Merged with `setdefault`: a word the window already says keeps its reading.
FACTS = {
    "p_perdida": "P de pérdida",
    "pbo_sobre_p95": "PBO sobre el p95 de su nulo",
    "bajo_p5": "Bajo el p5 de su nulo",
    "perverso": "Perverso",
    "mediana_exceso": "Mediana del exceso",
    "centro_exceso": "Exceso de la celda central",
    "l2_p_menos": "p− de L2",
    "p_menos": "p−",
    "p_mas": "p+",
}
KNOBS = {
    "block_weeks": "Semanas por bloque",
    "straddle_warn": "Aviso de fin de semana",
    "straddle_max": "Tope de fin de semana",
    "sqx_tolerance": "Tolerancia con SQX",
    "sqx_relative": "Tolerancia relativa con SQX",
    "skew_warn": "Aviso de asimetría",
    "charged": "Tramo ya cobrado",
    "median_low": "Mediana mínima del nulo",
    "median_high": "Mediana máxima del nulo",
    "p_perdida_fail": "P de pérdida: NO PASA",
    "p_perdida_limbo": "P de pérdida: LIMBO",
    "floor_per_param": "Suelo por parámetro",
    "floor_per_year": "Suelo por año",
    "min_variants": "Mínimo de variantes",
    "deltas": "Sharpe plantados",
    "share": "Fracción plantada",
    "bins": "Barras",
    "reach": "Alcance",
    "budget_s": "Presupuesto (s)",
    "min_common": "Variantes comunes mínimas",
    "max_ties": "Empates máximos",
    "min_weight": "Peso mínimo",
    "top_share": "Parte del top",
    "percentile": "Percentil",
    "min_rho": "ρ mínima",
    "rhos": "ρ plantadas",
    "relative": "Tolerancia relativa",
    "max_share": "Parte máxima",
    "runs": "Pasadas",
    "oos_pct": "% fuera de muestra",
    "modo_real": "Modo real",
}
LABELS = FACTS | {f"knob.{k}": v for k, v in KNOBS.items()}
LABELS["sqx.surfaces"] = "Superficies de mercado (paso 18.5)"
LABELS["sqx.wfmreading"] = "Lectura de la WFM (paso 19)"
