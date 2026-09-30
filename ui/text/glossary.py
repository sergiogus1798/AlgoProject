"""The one glossary of visible labels: a key a module writes → the Spanish words the window shows."""

import re

# Metric and column keys the window shows today, by the spelling their writer uses: SQX's
# metric names, the report columns of the studies, the gate's screens and the config knobs.
# Append new keys at the end (plan 24 §5): never change an existing one, a view may rely on it.
LABELS = {
    # SQX metrics, as the exports name them
    "Net profit": "Beneficio neto", "# of trades": "Operaciones",
    "Profit factor": "Profit Factor", "Sharpe Ratio": "Sharpe",
    "Ret/DD Ratio": "Retorno / DD", "Max DD %": "DD máximo %",
    "Winning Percent": "% ganadoras", "R Expectancy": "Esperanza en R",
    "Stability": "Estabilidad", "PSR": "PSR",
    # the columns the zones print
    "strategy": "Estrategia", "estrategia": "Estrategia", "strategy_build": "Estrategia en el build",
    "identity": "Identidad", "identidad": "Identidad", "murió en": "Murió en",
    "sobrevive": "Sobrevive", "verdict": "Veredicto", "reason": "Motivo", "tier": "Nivel",
    "confidence": "Confianza", "trades": "Operaciones", "family": "Familia",
    "composite": "Compuesto", "value": "Valor", "test": "Prueba", "flags": "Avisos",
    "warnings": "Avisos", "gate": "Puerta", "gates": "Puertas", "screen": "Criba",
    "passed": "Pasa", "entered": "Entraron", "died": "Murieron", "kind": "Tipo",
    "name": "Nombre", "note": "Nota", "nota": "Nota", "why": "Por qué", "runs": "Corridas",
    "markets": "Mercados", "market": "Mercado", "timeframe": "Timeframe",
    "net": "Neto", "net_5": "Neto p5", "pf": "PF", "pf_5": "PF p5", "psr": "PSR",
    "ret_dd": "Retorno / DD", "dd_pct": "DD %", "dd_pct_95": "DD % p95",
    "dd_pct_99": "DD % p99", "stitched_dd_pct": "DD % empalmado", "sharpe": "Sharpe",
    "sharpe_is": "Sharpe IS", "sharpe_oos": "Sharpe OOS", "oos_ratio": "Cociente OOS / IS",
    "oos_pct": "OOS %", "net_profit_oos": "Beneficio neto OOS", "retention": "Retención",
    "edge_r": "Ventaja en R", "real_r": "R real", "null_r": "R del nulo",
    "null_trades": "Operaciones del nulo", "p": "p", "p_min": "p mínimo",
    "p_median": "p mediano", "paired_p": "p emparejado", "rho": "ρ", "t": "t",
    "outlier_share": "Peso de los atípicos", "concentration": "Concentración",
    "years_positive": "Años positivos", "worst_year": "Peor año",
    "worst_pf": "Peor PF", "worst_market": "Peor mercado", "windows_ok": "Ventanas que pasan",
    "high_vol_net": "Neto en alta volatilidad", "inflation": "Inflación",
    "limit": "Límite", "vetoes": "Vetos", "under_alpha": "Bajo α",
    "paired_under_alpha": "Bajo α emparejado", "hold_median": "Duración mediana",
    "cost_rate": "Coste por operación", "slippage_decay": "Caída por slippage",
    "fill_error": "Error de llenado", "resolution": "Resolución", "reading": "Lectura",
    "mother": "Madre", "model": "Modelo", "parameter": "Parámetro", "paso": "Paso",
    "n_in": "N dentro", "n_out": "N fuera", "n_steps": "N pasos",
    "min_track_needed": "Historia mínima necesaria", "min_track_enough": "Historia suficiente",
    "stress_net_p5": "Neto p5 bajo estrés", "stress_cvar_dd_pct": "CVaR del DD % bajo estrés",
    # the gate's screens (studies/screening/gate/config.yaml)
    "presencia": "Presencia", "sanidad": "Sanidad", "estaticas": "Estáticas",
    "degradacion": "Degradación", "forma": "Forma", "mono": "Mono", "familia": "Familia",
    "redundancia": "Redundancia",
    # config knobs, section.knob as the drawer names them
    "null.draws": "Nulo · corridas", "null.chunk": "Nulo · corridas por lote",
    "draws": "Corridas", "chunk": "Corridas por lote", "seed": "Semilla",
    # Configuración SQX (plan 24, F9): the keys of assets/_build.yaml, _classes.yaml and the
    # globals of _policy.yaml, namespaced `sqx.` so a bare «build» elsewhere keeps its reading
    "sqx.complexity": "Complejidad de las reglas", "sqx.order_types": "Tipos de orden",
    "sqx.exits": "Salidas", "sqx.money_management": "Money management",
    "sqx.trading_options": "Opciones de trading", "sqx.engine": "Motor de backtest",
    "sqx.databank": "Databank", "sqx.precision": "Precisión",
    "sqx.crosschecks": "Crosschecks", "sqx.crossmarket": "Cross-market",
    "sqx.crosstf": "Cross-timeframe (CrossTF)", "sqx.mc_retest": "MC Retest",
    "sqx.wfc": "WFC", "sqx.cscv": "CSCV", "sqx.spp": "SPP", "sqx.wfm": "Walk Forward Matrix (WFM)",
    "sqx.forex": "Clase forex", "sqx.no_forex": "Clase no forex",
    "sqx.segments_default": "Tramos: qué es cada uno", "sqx.swap": "Swap",
    "sqx.universe": "Mercados de retest",
    "sqx.max_entry_conditions": "Máx. condiciones de entrada",
    "sqx.max_exit_conditions": "Máx. condiciones de salida",
    "sqx.lookback_bars": "Barras hacia atrás", "sqx.bars": "Salida por barras",
    "sqx.min_hours": "Horas mínimas", "sqx.max_hours": "Horas máximas",
    "sqx.by_condition": "Salida por condición", "sqx.condition_required": "Condición obligatoria",
    "sqx.stop_loss": "Stop loss", "sqx.profit_target": "Profit target",
    "sqx.trailing_stop": "Trailing stop", "sqx.move_sl_to_be": "SL a break-even",
    "sqx.method": "Método", "sqx.params": "Parámetros", "sqx.initial_capital": "Capital inicial",
    "sqx.max_drawdown": "Drawdown máximo", "sqx.ExitOnFriday": "Cerrar el viernes",
    "sqx.FridayExitTime": "Hora de cierre del viernes (s)",
    "sqx.max_strategies": "Máx. estrategias", "sqx.stop_condition": "Condición de parada",
    "sqx.build": "Construcción", "sqx.default": "Resto de tareas", "sqx.segment": "Tramo",
    "sqx.conditions": "Condiciones", "sqx.timeframes": "Timeframes extra",
    "sqx.simulations": "Simulaciones", "sqx.tasks": "Tareas", "sqx.title": "Título",
    "sqx.full_sample": "Muestra completa", "sqx.methods": "Métodos",
    "sqx.min_trades_total": "Mín. operaciones en total", "sqx.input": "Databank de entrada",
    "sqx.max_tests": "Máx. tests", "sqx.spread_pct": "Recorrido ± %", "sqx.step_pct": "Paso %",
    "sqx.costs_segment": "Tramo de costes", "sqx.period_type": "Tipo de periodo",
    "sqx.optimization_type": "Tipo de optimización", "sqx.wf_type": "Tipo de walk-forward",
    "sqx.distribution_pct": "Recorrido ± %", "sqx.oos_pct": "OOS %", "sqx.runs": "Pasadas",
    "sqx.start": "Desde", "sqx.stop": "Hasta", "sqx.step": "Paso",
    "sqx.threshold_pct": "Umbral de casilla %", "sqx.grid_passing_size": "Lado del rectángulo",
    "sqx.min_squares": "Mín. casillas aprobadas", "sqx.read": "Lee", "sqx.metric": "Métrica",
    "sqx.op": "Operador", "sqx.value": "Valor", "sqx.what": "Qué es", "sqx.spread": "Spread",
    "sqx.fields": "Campos", "sqx.unit": "Unidad", "sqx.sqx": "Ajuste de SQX", "sqx.note": "Nota",
    "sqx.commission": "Comisión", "sqx.field": "Campo", "sqx.sqx_method": "Método de SQX",
    # WFC and CSCV's study files (owner, 2026-09-28): the batch, the factory, the two readings
    "sqx.n_target": "Máx. variantes por madre", "sqx.variants": "Mín. variantes por madre",
    "sqx.strata": "Estratos", "sqx.neighbourhood": "Vecindad", "sqx.factorial": "Factorial",
    "sqx.coverage": "Cobertura", "sqx.min_span": "Recorrido mínimo ±", "sqx.plateau_share": "Meseta",
    "sqx.min_levels": "Mín. niveles", "sqx.max_levels": "Máx. niveles", "sqx.widen_step": "Ensanche",
    "sqx.max_span": "Recorrido máximo ±", "sqx.radius": "Radio", "sqx.frozen": "Congelados",
    "sqx.span": "Recorrido ±", "sqx.steps": "Pasos", "sqx.n": "Cuántos", "sqx.seed": "Semilla",
    "sqx.inert_pairs": "Pares inertes", "sqx.min_trades": "Mín. operaciones por lado",
    "sqx.split_mode": "Composición del corte", "sqx.rho_floor": "Suelo de ρ",
    "sqx.table_ends": "Filas por extremo", "sqx.period": "Periodo", "sqx.score": "Puntuación",
    "sqx.blocks": "Bloques (combinaciones)", "sqx.rules": "Reglas de selección",
    "sqx.random_draws": "Sorteos de la regla aleatoria", "sqx.bootstrap": "Remuestreos",
    "sqx.cluster_k_max": "Máx. clústeres", "sqx.why": "Por qué",
    "sqx.formula": "Fórmula", "sqx.slippage": "Slippage", "sqx.sqx_type": "Tipo de SQX",
    "sqx.purpose": "Para qué", "sqx.reserved_for": "Reservado a",
    "sqx.triple_swap_on": "Triple swap el", "sqx.rollout_hour": "Hora del rollover",
    "sqx.sqx_factory_default": "De fábrica en SQX",
    "sqx.default_multiples": "Múltiplos por defecto", "sqx.min": "Mínimo", "sqx.max": "Máximo",
    "sqx.min_distance": "Distancia mínima", "sqx.markets": "Con mercados adicionales",
    # the asset zone (plan 24, F8), namespaced `assets.` so no other zone inherits them
    "assets.spread": "Spread", "assets.spread_is": "Spread (IS)", "assets.spread_oos": "Spread (OOS)",
    "assets.spread_oos2": "Spread (OOS 2)", "assets.commission": "Comisión",
    "assets.slippage": "Slippage", "assets.slippage_is": "Slippage (IS)",
    "assets.slippage_oos": "Slippage (OOS)", "assets.slippage_oos2": "Slippage (OOS 2)",
    "assets.swap_long": "Swap (Long)", "assets.swap_short": "Swap (Short)",
    "assets.min_distance": "Min Distance", "assets.build": "Build", "assets.oos1": "OOS 1",
    "assets.oos2": "OOS 2", "assets.is": "IS", "assets.oos": "OOS", "assets.data": "Datos",
    "assets.points": "puntos", "assets.usd_per_lot": "USD por lote",
    "assets.pct_of_notional": "% del nocional", "assets.points_per_night": "puntos por noche",
    "assets.pct_annual": "% anual", "assets.SizeBased": "USD por lote",
    "assets.PercentageBased": "% del nocional", "assets.sqx_now": "SQX hoy", "assets.use": "Usar",
    "assets.unit": "Unidad", "assets.field": "Campo", "assets.min": "Mín", "assets.max": "Máx",
    "assets.range": "Rango", "assets.family": "Family", "assets.structural": "Structural",
    "assets.forex": "Forex", "assets.no_forex": "No forex",
    # the databank panel (plan 24, F3b): verdict.csv columns and batch summaries it shows
    "cleared": "Mercados superados", "fraction": "Fracción", "binding": "Tramo que manda",
    "blocked_by": "Bloqueada por", "seen": "Visto", "baseline": "Referencia",
    "control": "Control", "pf_cv": "CV del PF", "missing": "Faltan", "broken": "Se rompe en",
    "score": "Puntuación", "point": "Punto", "surface": "Superficie", "temporal": "Temporal",
    "variants": "Variantes", "dropped": "Descartadas", "r2": "R²", "gap": "Hueco",
    "rho_median": "ρ mediana", "drift_median": "Deriva mediana", "roughness": "Rugosidad",
    # the study result's drawings (plan 24, F5): densities, grids side by side, partial re-runs
    "grid.mark": "La celda de la madre (sus parámetros)", "grid.empty": "Sin dato",
    "grid.shared": "Escala común a las rejillas:", "density.shift": "Desplazamiento de la mediana",
    "density.ks": "p del KS (misma distribución)", "density.union": "Percentiles de la unión",
    "density.show": "Muestras a la vista", "markets.pick": "Mercados a la vista (hasta 3)",
    "markets.consensus": "Consenso de todos los mercados", "partial.beside": "Ver al lado del guardado",
    "partial.merged": "Ver fusionado", "partial.stored": "Volver al guardado",
    "partial.head": "Re-ejecución parcial", "screen.report": "Informe de lo que ves",
    # the Estrategia page (plan 24, F4): signal names of a .sqx and the two curves
    "LongEntrySignal": "Entrada larga", "ShortEntrySignal": "Entrada corta",
    "LongExitSignal": "Salida larga", "ShortExitSignal": "Salida corta",
    "curve.sqx": "SQX (curva diaria)", "curve.real": "spread y slippage reales",
    # the configuration knobs by part (encargo 24, F15): `knob()` labels each dotted part of
    # a knob key here first, so a section word reads the same in the rail and the drawer
    "knob.nulls": "Nulos", "knob.null": "Nulo", "knob.run": "Ejecución", "knob.ingest": "Ingesta",
    "knob.study": "Estudio", "knob.benchmark": "Referencia", "knob.bootstrap": "Bootstrap",
    "knob.sweep": "Barrido", "knob.joint": "Conjunta", "knob.equity": "Equity",
    "knob.paired": "Emparejado", "knob.stress": "Estrés", "knob.usable": "Utilizable",
    "knob.read": "Lectura", "knob.design": "Diseño", "knob.stability": "Estabilidad",
    "knob.verdict": "Veredicto", "knob.global": "General", "knob.general": "General",
    "knob.subsets": "Subconjuntos", "knob.scale": "Escala", "knob.assets": "Activos",
    "knob.day": "Día", "knob.safety": "Margen de seguridad", "knob.reprice": "Reajuste",
    "knob.band": "Banda", "knob.onboard": "Alta de un activo", "knob.segments": "Tramos",
    "knob.segment": "Tramo", "knob.levels": "Niveles", "knob.recon": "Reconstrucción",
    "knob.scenario": "Escenario", "knob.fragility": "Fragilidad", "knob.modes": "Modos",
    "knob.attribution": "Atribución", "knob.evidence": "Evidencia", "knob.scoring": "Nota",
    "knob.grid": "Rejilla", "knob.window": "Ventana", "knob.sessions": "Sesiones",
    "knob.controls": "Controles", "knob.strata": "Estratos", "knob.portfolio": "Cartera",
    "knob.exposure": "Exposición", "knob.diagnostics": "Diagnóstico", "knob.metric": "Métrica",
    "knob.sample": "Muestra", "knob.symbol": "Símbolo", "knob.feed": "Feed", "knob.bars": "Velas",
    "knob.ticks": "Ticks", "knob.min_trades": "Mín. operaciones", "knob.alpha": "α",
    "knob.tolerance": "Tolerancia", "knob.action": "Acción", "knob.factor": "Factor",
    "knob.capital": "Capital", "knob.workers": "Procesos", "knob.blocks": "Bloques",
    "knob.period": "Periodo", "knob.percentiles": "Percentiles",
    "knob.split_mode": "Modo de corte", "knob.rho_floor": "Suelo de ρ",
    "knob.statistic": "Estadístico", "knob.rung": "Peldaño", "knob.sizing": "Tamaño de posición",
    "knob.fwer": "FWER", "knob.reps": "Repeticiones", "knob.models": "Modelos",
    "knob.reference": "Referencia", "knob.steps": "Pasos", "knob.kind": "Tipo",
    "knob.draws": "Corridas", "knob.seed": "Semilla", "knob.chunk": "Corridas por lote",
    "knob.timeframe": "Timeframe", "knob.keep": "Condición", "knob.value": "Valor",
    "knob.why": "Por qué", "knob.min_retention": "Retención mínima", "knob.min_t": "t mínimo",
    "knob.min_years_positive": "Mín. años positivos",
    "knob.max_concentration": "Concentración máxima", "knob.max_dd_ratio": "Máx. DD / esperado",
    "knob.max_p": "p máximo", "knob.headline": "Titular", "knob.starting": "Cuenta inicial",
    "knob.starting_equity": "Cuenta inicial", "knob.risk_per_trade": "Riesgo por operación",
    "knob.n_sims": "Simulaciones", "knob.n_resamples": "Remuestreos",
    "knob.confidence": "Confianza", "knob.method": "Método", "knob.tiers": "Cortes de nivel",
    "knob.weights": "Pesos", "knob.min_pf": "PF mínimo", "knob.commission": "Comisión",
    "knob.swap": "Swap", "knob.triple_swap_on": "Triple swap el", "knob.build": "Construcción",
    "knob.build_to": "Construcción hasta", "knob.oos1": "OOS1", "knob.oos2": "OOS2",
    "knob.model": "Modelo", "knob.candidates": "Candidatos", "knob.split": "Año de corte",
    "knob.fixed": "Fijado", "knob.quantiles": "Cuantiles", "knob.min_minutes": "Mín. minutos",
    "knob.judge": "Juzga contra", "knob.near_minutes": "Minutos de cercanía",
    "knob.batch_draws": "Corridas por tanda", "knob.batch_cells": "Celdas por tanda",
    "knob.chunk_trades": "Operaciones por lote", "knob.percentile_set": "Percentiles guardados",
    "knob.tile_bytes": "Bytes por franja", "knob.max_workers": "Máx. procesos",
    "knob.trim": "Recorte", "knob.best_months": "Mejores meses", "knob.open": "Apertura",
    "knob.close": "Cierre", "knob.zone": "Zona horaria", "knob.report": "Informe",
    "knob.pieces": "Piezas", "knob.breakeven": "Break-even",
    "knob.companion_metrics": "Métricas acompañantes", "knob.drop_future": "Descartar el futuro",
    "knob.cscv": "CSCV", "knob.stepm": "StepM", "knob.monkey": "Nulo del mono", "knob.stop": "Stop",
    "knob.shape": "Forma", "knob.trend": "Tendencia", "knob.volatility": "Volatilidad",
    "knob.constancy": "Constancia", "knob.family_b": "Familia B", "knob.family_c": "Familia C",
    "knob.family_d": "Familia D", "knob.family_e": "Familia E", "knob.neighbourhood": "Vecindad",
    "knob.surrogate": "Sustituto", "knob.ensemble": "Conjunto", "knob.transfer": "Transferencia",
    "knob.proof": "Prueba", "knob.barrier": "Barrera", "knob.statistics": "Estadísticos",
    "knob.dependence": "Dependencia", "knob.breaks": "Rupturas", "knob.delay": "Retraso",
}

# Words a humanised key spells its own way: acronyms in capitals, a few English words in Spanish.
WORDS = {"null": "nulo", "r": "R", "is": "IS", "oos": "OOS", "oos1": "OOS1", "oos2": "OOS2", "pf": "PF", "dd": "DD",
            "psr": "PSR", "atr": "ATR", "mae": "MAE", "mfe": "MFE", "sqx": "SQX", "wfc": "WFC",
            "wfm": "WFM", "spp": "SPP", "mc": "MC", "cvar": "CVaR", "ks": "KS", "id": "ID"}
KEY = re.compile(r"[\w.]+")     # an identifier a module wrote, not a phrase a person did


def label(key: object) -> str:
    """The words the window shows for one key.

    Args:
        key: A metric, column or knob key as its writer spells it.

    Returns:
        Its glossary entry; otherwise, for an identifier (`null.chunk3_traits`), its parts
        split on `.`, `_` and camelCase, acronyms in capitals, joined by spaces; for a phrase, the
        phrase itself. Always with an initial capital.
    """
    key = str(key)
    if key in LABELS:
        return LABELS[key]
    if KEY.fullmatch(key):
        split = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", key)          # camelCase too: isOos
        key = " ".join(WORDS.get(w.lower(), w) for w in re.split(r"[._]+", split) if w)
        # The owner's name for it, in English on every screen (2026-09-28): `profit_factor_is`.
        key = re.sub(r"(?i)\bprofit factor\b", "Profit Factor", key)
    return key[:1].upper() + key[1:]


def knob(key: object) -> str:
    """The words for a configuration knob: each dotted part through `knob.<part>`, then `label`.

    Args:
        key: A knob key as `ui.daemon.results.knobs` spells it (`nulls.draws`,
            `presencia.kind`), or the part of it under a section already shown.

    Returns:
        Its glossary entry when the whole key has one; otherwise its parts joined by « › »
        («Nulos › Corridas», «Presencia › Tipo»). Never the raw dotted key.
    """
    key = str(key)
    if key in LABELS:
        return LABELS[key]
    return " › ".join(LABELS.get(f"knob.{part}") or label(part) for part in key.split("."))
