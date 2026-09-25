"""The words the owner reads: every fired check as a sentence, and why the verdict is what it is."""

from portfolio.common.monteCarlo.model import stress
from portfolio.common.monteCarlo.verdict import scoring

LABELS = {"net": "Beneficio neto", "return_pct": "Retorno", "dd": "Drawdown $",
          "dd_pct": "Drawdown %", "ret_dd": "Ret/DD", "sharpe": "Sharpe por operación",
          "pf": "Profit factor", "losing_run": "Racha perdedora"}
UNITS = {"net": "USD", "return_pct": "%", "dd": "USD", "dd_pct": "%", "ret_dd": "",
         "sharpe": "", "pf": "", "losing_run": ""}
# stress.MODELS is code and stays in English; the report is read in Spanish.
MODELS_ES = {"skip": "Entradas que el sistema real no llega a tomar",
             "cost_shock": "Comisión y swap hasta el doble de lo que SQX cobró",
             "fill_degrade": "Ejecuciones que devuelven parte de lo que la propia operación "
                             "ya había cedido",
             "spread_widen": "Un spread más ancho que el fijo que supuso el backtest"}

# One sentence per check that can fire, with the number that fired it. Written so that the
# sentence alone says what to do about it.
FLAGS = {
    "dd_99": "El drawdown del percentil 99 es {value:.1%} de la cuenta, por encima del techo "
             "de supervivencia {limit:.0%}. Con este riesgo por operación la cuenta no aguanta "
             "la peor de cien reordenaciones.",
    "inflation": "El drawdown del backtest fue afortunado: reordenando las mismas operaciones "
                 "sale {value:.1f} veces mayor (límite {limit:.0f}).",
    "inflation_watch": "El drawdown reordenado es {value:.1f} veces el del backtest; por encima "
                       "de {limit:.1f} conviene vigilarlo, no descartarlo.",
    "net_5": "En 1 de cada 20 remuestreos el beneficio es {value:,.0f} $, es decir negativo: "
             "el resultado depende de qué operaciones salieron.",
    "pf_5": "El profit factor del percentil 5 es {value:.2f}, por debajo de {limit:.2f}.",
    "outlier": "La mejor operación aporta el {value:.0%} del beneficio (límite {limit:.0%}). "
               "Mira las mayores ganadoras antes de creerte el total.",
    "oos_red": "El Sharpe mediano fuera de muestra es el {value:.0%} del de dentro. Eso es "
               "optimismo que el test de decaimiento no recogió.",
    "oos_amber": "El Sharpe fuera de muestra cae al {value:.0%} del de dentro (aviso por debajo "
                 "de {limit:.0%}).",
    "skip": "Perdiendo entradas al azar el beneficio queda en el {value:.0%} del real, por "
            "debajo del {limit:.0%} exigido.",
    "fill_degrade": "Con ejecuciones peores el beneficio queda en el {value:.0%} del real "
                    "(mínimo {limit:.0%}).",
    "cost_shock": "Con costes hasta el doble, el profit factor del percentil 5 baja a "
                  "{value:.2f} (mínimo {limit:.2f}).",
    "spread_widen": "Con un spread más ancho el profit factor del percentil 5 baja a "
                    "{value:.2f} (mínimo {limit:.2f}).",
    "high_vol": "En el tercil de volatilidad alta la mediana remuestreada es {value:,.0f} $: "
                "el sistema no gana en el régimen que más le va a tocar.",
    "dead_block": "Hay un bloque de 24 meses con mediana negativa ({value:,.0f} $): un periodo "
                  "entero en el que la estrategia no funcionó.",
    "windows": "Sólo el {value:.0%} de las ventanas móviles aguanta en positivo en su percentil "
               "5 (se pide {limit:.0%}).",
    "concentration": "El {value:.0%} del beneficio sale de un solo tercil de volatilidad "
                     "(límite {limit:.0%}).",
    "psr": "La PSR es {value:.3f}: con este número de operaciones y esta forma de la "
           "distribución, no se puede descartar que el edge sea cero.",
    "psr_amber": "La PSR es {value:.3f}, por debajo del objetivo {limit:.2f}.",
    "cost_file": "El coste modelado desde assets/ es {value:.2f} veces el que SQX cobró de "
                 "verdad. Las pruebas de la familia C se leen con esa reserva.",
    "sample": "Con {value:.0f} operaciones alguno de los números que deciden no es fiable. "
              "El veredicto se queda en INCONCLUSIVE."}

# What to call a check where it is named rather than explained, e.g. the verdict's failed
# list. Family C reuses stress.TITLES so the name is not typed twice.
TITLES = {**stress.TITLES,
          "dd_99": "Drawdown percentil 99", "inflation": "Drawdown inflado",
          "inflation_watch": "Drawdown inflado (aviso)", "net_5": "Beneficio percentil 5",
          "pf_5": "Profit factor percentil 5", "outlier": "Mejor operación",
          "oos_red": "Caída OOS", "oos_amber": "Caída OOS (aviso)",
          "high_vol": "Volatilidad alta", "dead_block": "Bloque muerto",
          "windows": "Ventanas móviles", "concentration": "Concentración por régimen",
          "psr": "PSR", "psr_amber": "PSR (aviso)", "cost_file": "Coste modelado",
          "sample": "Muestra insuficiente"}


def title(flag: dict) -> str:
    """One fired check's name, for a heading — never the internal key.

    Args:
        flag: What gates.check() produced.

    Returns:
        The Spanish name a reader can act on, e.g. "Ejecuciones degradadas" rather than
        "fill_degrade".
    """
    return TITLES[flag["test"]]


def sentence(flag: dict) -> str:
    """One fired check, in plain language, with its own number inside.

    Args:
        flag: What gates.check() produced.

    Returns:
        The sentence. A failure whose number is not in the sentence is a failure nobody
        can act on.
    """
    return FLAGS[flag["test"]].format(value=flag["value"], limit=flag["limit"])


def rationale(result: dict, verdict: dict) -> str:
    """Why the verdict is what it is, naming the metric that decided it.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.

    Returns:
        Two sentences: the binding constraint with its number, and what would have to
        change. The composite is never the explanation — the constraint is.
    """
    binding = verdict["binding"]
    if binding["gate"]:
        return ("Lo que decide: " + sentence(binding) + " Mientras esa prueba no pase, "
                "el compuesto no significa nada.")
    family = binding["family"]
    return (f"Ninguna prueba veta. Lo que limita la nota es la familia {family} "
            f"({binding['value']:.0f} sobre 100): {scoring.BUILT_FROM[family]}. "
            f"El compuesto es {verdict['composite']:.0f}.")
