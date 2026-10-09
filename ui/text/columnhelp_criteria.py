"""The «?» and the header of the criteria-metric columns (owner, 2026-10-04: computed, shown, no threshold)."""

import re

NO = " Sin umbral todavía: no cambia ningún veredicto."
METRIC = {"Net_Profit": "Net Profit", "Profit_Factor": "PF", "Ret_DD": "Ret/DD",
          "Max_Drawdown": "DD", "Sharpe": "Sharpe", "Sortino": "Sortino", "R_Edge": "R/Edge"}
TOKEN = "(" + "|".join(METRIC) + ")"
WFC_COMP = (" Composición {0}: c1 = build+oos1 → oos2, c2 = build → oos1+oos2, "
            "c3 = build → oos2.")
# (study, pattern of the field) → (header, sentence); {0}, {1} are the pattern's groups, said
# as the panel says them.
FAMILIES = [
    ("spp", rf"distancia_pct_(IS|OOS1)_{TOKEN}", "Δ% {0} {1}",
     "(Original − mediana) / |mediana| de sus permutaciones {0}, en %, con signo: {1}. El "
     "criterio heredado de SQX es que quede dentro de ± X %. Premia la poca dispersión; mira "
     "también la distancia en IQR."),
    ("spp", rf"distancia_IQR_(IS|OOS1)_{TOKEN}", "ΔIQR {0} {1}",
     "Distancia del original a la mediana de sus permutaciones {0}, en rangos intercuartílicos "
     "de la rejilla: {1}. No depende de lo grande que sea la mediana."),
    ("spp", rf"decaimiento_{TOKEN}", "Decaim. {0}",
     "Mediana(OOS1) / mediana(IS) de las permutaciones: {0}. Un cociente de medianas (IS y OOS1 "
     "no comparten permutaciones). 1 = no decae. Vacío si la mediana IS no supera su suelo. "
     "Diagnóstico: con 4 años de OOS1 no distingue una familia sin ventaja."),
    ("spp", rf"A_{TOKEN}", "A OOS/IS {0}",
     "A de Vargha–Delaney: probabilidad de que una permutación OOS1 supere a una IS, en {0}. "
     "0,5 = iguales; por debajo, decae. Tamaño de efecto, no p-valor. Diagnóstico."),
    ("spp", rf"Wasserstein_{TOKEN}", "W/IQR {0}",
     "Distancia de Wasserstein entre las permutaciones IS y OOS1 dividida por el IQR de IS, "
     "en {0}: cuántos IQR separan las dos distribuciones. 0 = iguales; bilateral. Diagnóstico."),
    ("wfc", r"wfc\.(c[123])\.rho", "ρ {0}",
     "ρ de Spearman entre el exceso por año de dentro y el de fuera. De −1 a +1 (+1 mismo "
     "orden, 0 ningún parecido, −1 invertido): un coeficiente, no un porcentaje." + WFC_COMP),
    ("wfc", r"wfc\.(c[123])\.p_mas", "p+ {0}",
     "Fracción de sorteos del nulo de volteo con una ρ igual o mayor que la observada. "
     "Pequeño = el orden se repite fuera más que por ruido." + WFC_COMP),
    ("wfc", r"wfc\.(c[123])\.p_menos", "p− {0}",
     "Fracción de sorteos del nulo con una ρ igual o menor que la observada. Pequeño = lo "
     "mejor de dentro tiende a ser lo peor de fuera." + WFC_COMP),
    ("wfc", r"wfc\.(c[123])\.nulo_p5", "Nulo p5 {0}",
     "Percentil 5 de la ρ en el nulo de volteo (la misma familia sin ventaja fuera). Una ρ "
     "entre el p5 y el p95 no se distingue del ruido." + WFC_COMP),
    ("wfc", r"wfc\.(c[123])\.nulo_p95", "Nulo p95 {0}",
     "Percentil 95 de la ρ en el nulo de volteo. Una ρ entre el p5 y el p95 no se distingue "
     "del ruido." + WFC_COMP),
    ("wfc", r"wfc\.(c[123])\.nivel_top", "Nivel top {0}",
     "Mediana del exceso por año fuera de las variantes del top de dentro. Por encima de 0, "
     "lo que elegiría un optimizador gana fuera." + WFC_COMP),
    ("wfc", r"wfc\.(c[123])\.p_nivel", "p nivel {0}",
     "Fracción de sorteos del nulo de volteo (los mismos del orden) cuya mediana del top es "
     "igual o mayor que la observada. Pequeño (≤ 0,05) = el top gana fuera más que por ruido. "
     "Sólo se anota: ya no decide el estado." + WFC_COMP),
    ("wfc", r"wfc\.(c[123])\.nivel_todas", "Nivel todas {0}",
     "Mediana del exceso por año fuera de todas las variantes medidas." + WFC_COMP),
    ("wfc", r"wfc\.(c[123])\.r_sel", "R_sel {0}",
     "Retención de la prima de selección: (nivel del top − nivel de todas) fuera ÷ lo mismo "
     "dentro. 1 = se conserva; 0 = elegir no sirve; negativo = perverso. Vacío si la prima "
     "de dentro es casi nula." + WFC_COMP),
    ("mcRetest", r"percentil_original_estres", "Percentil orig. estrés",
     "Porcentaje de re-ejecuciones del estrés combinado con menos Net Profit que el backtest "
     "original. 50 = el original es un resultado típico; cerca de 100 = casi ninguna lo "
     "alcanza. Diagnóstico: el estrés sortea costes peores, así que supera 50 por construcción."),
    ("mcRetest", r"brecha_mediana_pct_estres", "Brecha med. % estrés",
     "(Mediana de las re-ejecuciones del estrés combinado − original) / |original|, en %. "
     "−30 = la re-ejecución típica gana un 30 % menos. Vacío si el original está cerca de cero."),
    ("mcRetest", r"distancia_IQR_estres", "Dist. IQR estrés",
     "Original − mediana de las re-ejecuciones del estrés combinado, en rangos "
     "intercuartílicos de las re-ejecuciones (1 IQR ≈ 1,35 sigmas)."),
]
SHOWN = {"oos1": "OOS1", "oos2": "OOS2", "build": "IS", "minimo": "mínimo"}


def criteria(study: str, field: str) -> tuple[str, str] | None:
    """The header and the sentence of one criteria-metric column, None for any other column.

    Args:
        study: The catalogue key.
        field: The column's field as the study writes it.
    """
    for owner, pattern, head, text in FAMILIES:
        if owner == study and (got := re.fullmatch(pattern, field)):
            said = [SHOWN.get(g, METRIC.get(g, g)) for g in got.groups()]
            return head.format(*said), text.format(*said) + NO
    return None
