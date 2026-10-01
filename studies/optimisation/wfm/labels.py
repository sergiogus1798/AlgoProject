"""The Spanish name and the one-sentence meaning of every WFM objective the window shows."""

FAMILY = {"oos": "WF", "stability": "Estabilidad", "score": "Score", "special": ""}
METRIC = {"NetProfit": "beneficio neto", "ProfitFactor": "PF", "SharpeRatio": "Sharpe",
          "DrawdownPct": "DD máx. %", "Drawdown": "DD máx.", "NumberOfTrades": "nº de operaciones",
          "WFPctOfProfitableRuns": "% de pasadas rentables",
          "WFMaxProfitByRunInPct": "mayor beneficio de una pasada, % del total",
          "WFMinTradesInRun": "mínimo de operaciones en una pasada",
          "WFMaxPctDDbyRun": "peor DD % de una pasada",
          "WFMaxDDbyRun": "peor DD de una pasada (USD)",
          "WFMaxProfitByRun": "mayor beneficio de una pasada (USD)",
          "WFMaxStagnationInPct": "mayor estancamiento de una pasada, %"}
MEANING = {
    "oos": "La métrica sobre todas las pasadas fuera de muestra de la celda, encadenadas.",
    "stability": "Lo que la métrica dio fuera de muestra frente a lo que dio en la optimización, "
                 "×100, sin el último tramo; el beneficio, las operaciones y el DD en dinero se "
                 "dividen antes por días. 100 = rindió fuera igual que dentro.",
    "score": "La métrica del walk-forward entero de la celda frente al backtest original con "
             "parámetros fijos, ×100. Por encima de 100, reoptimizar mejoró a no tocar nada.",
    "WFPctOfProfitableRuns": "Qué parte de las pasadas fuera de muestra cerró en positivo.",
    "WFMaxProfitByRunInPct": "Cuánto del beneficio total vino de la mejor pasada: alto = el "
                             "resultado depende de un solo tramo.",
    "WFMinTradesInRun": "Las operaciones de la pasada más pobre: pocas = esa pasada no dice nada.",
    "WFMaxPctDDbyRun": "El peor drawdown en % que tuvo una sola pasada fuera de muestra.",
    "WFMaxDDbyRun": "El peor drawdown en dinero que tuvo una sola pasada fuera de muestra.",
    "WFMaxProfitByRun": "El beneficio de la mejor pasada fuera de muestra.",
    "WFMaxStagnationInPct": "El estancamiento más largo de una pasada, en % de su duración.",
    "param_stability": "Estabilidad de parámetros que SQX guarda por celda (0-1): cuánto se "
                       "parecen los parámetros elegidos de un tramo a otro."}
OP = {">": ">", "<": "<", ">=": "≥", "<=": "≤", "=": "=", "==": "="}


def name(family: str, metric: str) -> str:
    """«Estabilidad del PF», «WF beneficio neto», «% de pasadas rentables»."""
    if family == "special" or metric.startswith("WF"):
        return METRIC.get(metric, metric)
    if family == "stability" and metric == "NetProfit":
        return "Estabilidad del beneficio neto (eficiencia WF)"
    joiner = " del " if family in ("stability", "score") else " "
    return f"{FAMILY[family]}{joiner}{METRIC.get(metric, metric)}"


def meaning(family: str, metric: str) -> str:
    """One sentence for the «?» of an objective."""
    if family == "special" or metric.startswith("WF"):
        return MEANING.get(metric, "")
    extra = (" Es la eficiencia walk-forward de Pardo: por debajo de 50-60 el sistema pierde "
             "en vivo la mitad de lo que promete al optimizarse."
             if family == "stability" and metric == "NetProfit" else "")
    return MEANING[family] + extra


def condition(c: dict) -> str:
    """«Estabilidad del PF > 60»."""
    return f"{name(c['family'], c['metric'])} {OP[c['op']]} {c['threshold']:g}"
