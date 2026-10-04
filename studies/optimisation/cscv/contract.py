"""The CSCV as the contract's blocks: where the chosen variant landed, and what choosing cost."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope

PERIODO = {"W": "semanales", "ME": "mensuales", "D": "diarios"}
# Periods a year, to annualise a per-period Sharpe/Sortino for display only (owner, 2026-09-30
# §8.4 «Sharpe anual en todo el CSCV»): a constant factor moves no rank, so no PBO. The CSCV
# ranks daily since 2026-10-01 (`config.yaml`), hence √252; the factor follows `cscv.period`
# because annualising with another period's factor would over-state the number.
PERIODS_YEAR = {"W": 52.0, "ME": 12.0, "D": 252.0}
SCORE_LABEL = {"sharpe": "Sharpe", "sortino": "Sortino"}
CALL = {"primer_orden": "gana siempre", "segundo_orden": "gana en promedio",
        "ninguna": "no gana"}
# Which rules are Bailey, Borwein, López de Prado and Zhu's and which this project added.
ORIGIN = {"argmax": "paper", "plateau_centre": "extensión"}
NAME = {"argmax": "Argmax", "plateau_centre": "Plateau center"}


def pct(x: float) -> str:
    """A fraction as «29,2 %», the way the owner reads a percentage."""
    return f"{x:.1%}".replace(".", ",").replace("%", " %")


def dec(x: float, signed: bool = False) -> str:
    """A number with two decimals and a comma: «+0,60»."""
    return f"{x:+.2f}".replace(".", ",") if signed else f"{x:.2f}".replace(".", ",")


METHOD = ("Método CSCV (Combinatorially Symmetric Cross-Validation) de Bailey, Borwein, "
          "López de Prado y Zhu, «The Probability of Backtest Overfitting» (2014).")
PBO_PLAIN = ("El PBO (probabilidad de sobreajuste del backtest) es la fracción de formas de "
             "partir la historia en dos mitades en que la variante que la regla eligió como la "
             "mejor en una mitad quedó por debajo de la mediana en la otra. Por debajo del 50 % "
             "elegir así supera al azar (Pass); por encima, elegir así es peor que no elegir "
             "(Fail).")
GLOSSARY = [
    {"term": "CSCV", "text": METHOD + " Parte la historia en bloques, toma la mitad de ellos "
     "como dentro de muestra y la otra mitad como fuera, y repite con todas las combinaciones."},
    {"term": "PBO", "text": PBO_PLAIN + " Método de López de Prado y colegas: "
     "rendimientos DIARIOS de cada variante "
     "(todos los días de mercado, también los de P&L cero), 16 bloques, las C(16,8) = 12.870 "
     "particiones, y el Sharpe de cada mitad."},
    {"term": "Percentil OOS", "text": "En qué percentil del ranking real fuera de muestra cayó "
     "lo que la regla habría elegido. 50 es lo que da elegir a ciegas."},
    {"term": "Pendiente", "text": "Extensión de este proyecto: cuánto del orden dentro de "
     "muestra se conserva fuera, ajustado sobre todas las variantes de cada partición. "
     "Sobre ruido puro sale 0. Es un "
     "número distinto del de «Degradación IS → OOS»: ese solo mira la variante elegida en "
     "cada partición, este los mira todos."},
    {"term": "Pierde", "text": "La probabilidad de pérdida del paper: en qué fracción de las "
     "particiones lo elegido terminó la mitad reservada en pérdidas. El PBO habla de puesto; "
     "esto, de dinero."},
    {"term": "Degradación IS → OOS", "text": "La regresión del paper: el Sharpe fuera de "
     "muestra de lo elegido contra su Sharpe dentro, una nube de puntos con un punto por "
     "partición. Anualizado ×√252 solo para leerlo: el factor no cambia ningún puesto."},
    {"term": "Vs. la mediana", "text": "Extensión de este proyecto: si elegir con la regla "
     "bate a quedarse con la combinación del medio, en toda la distribución o sólo en "
     "promedio (dominancia estocástica de primer y segundo orden)."},
    {"term": "Sortino", "text": "Extensión de este proyecto: el desplegable «Puntuación» "
     "vuelve a correr todo ordenando por Sortino en vez de por el Sharpe del paper."},
    {"term": "Argmax", "text": "Coger sin más el punto de mayor puntuación dentro de muestra. "
     "Es la regla original de Bailey, Borwein, López de Prado y Zhu (CSCV, 2014): λ es el "
     "logit del rango relativo fuera de muestra del punto elegido, PBO = P(λ ≤ 0)."},
    {"term": "Plateau center", "text": "Extensión de este proyecto, no del paper original: "
     "coger el punto cuyo entorno (él y sus vecinos hasta el radio del plateau) puntúa mejor "
     "en promedio, no el pico aislado. Se lee igual que Argmax: un PBO BAJO es bueno. Si "
     "baja mucho respecto a Argmax, el pico de la superficie era suerte y la meseta que lo "
     "rodea sí aguanta; si es parecido o peor, suavizar no compra nada."},
    {"term": "Radio del plateau", "text": "Hasta dónde llega «el entorno» de Plateau center: "
     "niveles de la rejilla de parámetros, en cada parámetro a la vez. Con 1 es el punto y "
     "sus vecinos inmediatos; con 2, dos pasos más lejos. Es un parámetro de entrada del "
     "estudio (cscv.plateau_radius)."}]


def verdict(found: dict, result: dict) -> dict:
    """The head rule's PBO as the call, every rule as a part, every PBO as a one-decimal %.

    `score` and the parts' `value` stay empty on purpose: the window prints a number there
    raw (0.07739), and a PBO reads as a percentage. The raw numbers are in `cscv.json`.
    """
    head = next(iter(found))
    pbo = found[head]["pbo"]
    return blocks.verdict(
        f"PBO {pct(pbo)} con {NAME[head]}", "fail" if pbo > 0.5 else "pass",
        f"Las {result['n']} variantes valen {result['n_clusters']} pruebas independientes; con "
        f"ese recuento el Sharpe del mejor sobrevive con probabilidad {pct(result['dsr'])} "
        f"(DSR). De una mitad a la otra el orden se conserva con pendiente "
        f"{dec(result['slope'], True)} (ajustada sobre todas las variantes, no solo la elegida; "
        f"extensión de este proyecto). Radio del plateau: {result['plateau_radius']}. "
        "Método de López de Prado y colegas (CSCV).",
        None, [{"label": f"{NAME[name]}: PBO {pct(f['pbo'])}",
                "state": "fail" if f["pbo"] > 0.5 else "pass", "value": None,
                "note": f"pierde {pct(f['prob_loss'])} · {CALL[f['dominance']]}"}
               for name, f in found.items()])


def rule_table(found: dict, radius: int) -> dict:
    """The rules side by side, PBO and «pierde» written as one-decimal percentages."""
    return {**blocks.table("Regla a regla", pd.DataFrame(
        [[f"{NAME[name]} ({ORIGIN[name]})", pct(f["pbo"]),
          "Fail" if f["pbo"] > 0.5 else "Pass", f["pct_oos"],
          f["ci95"][0], f["ci95"][1],
          pct(f["prob_loss"]), CALL[f["dominance"]]] for name, f in found.items()],
        columns=["Regla", "PBO", "Resultado", "Percentil OOS", "IC 95 % desde", "Hasta",
                 "Pierde", "Vs. la mediana"]),
        note=f"Radio del plateau: {radius} (niveles de la rejilla en cada parámetro; "
             "solo afecta a Plateau center)."),
        "help": ["Argmax es la regla original del CSCV de Bailey, Borwein, López de Prado y "
                 "Zhu; Plateau center es una extensión de este proyecto — glosario.",
                 PBO_PLAIN,
                 "Pass si el PBO es del 50 % o menos, Fail si pasa del 50 %.",
                 "Extensión: sobre la partición cronológica real, no sobre las "
                 "particiones combinatorias.",
                 None, None, "La probabilidad de pérdida del paper.",
                 "Extensión: dominancia estocástica frente a la variante mediana."]}


def tabs(runs_by_score: dict, found_by_score: dict, result: dict, default_score: str) -> list[dict]:
    """λ per rule and score, the rules side by side, and the IS → OOS degradation.

    Args:
        runs_by_score: `{"sharpe": {rule: DataFrame}, "sortino": {...}}`, what `cscv.run`
            returned per rule under each score — both always computed (owner, 2026-09-30
            §8.4), so the window's selector switches without calling the study again
            (CONTRACT §1 «selectors»).
        found_by_score: The same shape, what `summary.everything` | `cost.cost` returned.
        result: The flat result dict `report.py` writes to `cscv.json`.
        default_score: `cscv.score` from config — which combination the selector opens on.

    Returns:
        Two tabs, both carrying a "score" selector over every block.
    """
    head = next(iter(runs_by_score[default_score]))
    factor = PERIODS_YEAR.get(result["period"], 52.0) ** 0.5
    selector = {"key": "score", "label": "Puntuación",
                "options": [SCORE_LABEL[s] for s in runs_by_score],
                "default": SCORE_LABEL[default_score],
                "help": "Sharpe cuenta toda la dispersión; Sortino solo la de las pérdidas. "
                        "Las dos regla y particiones son las mismas; solo cambia con qué se "
                        "mide «mejor»."}
    lambda_blocks, decay_blocks = [], []
    for score_key, runs in runs_by_score.items():
        label = SCORE_LABEL[score_key]
        found = found_by_score[score_key]
        lambda_blocks += [
            {**blocks.distribution(f"λ — {NAME[name]}", "", r["lam"].to_numpy(), 0.0,
                                   f"PBO {pct(found[name]['pbo'])}: la parte a la izquierda "
                                   f"del cero."), "mark": "Corte", "select": {"score": label},
             "help": f"{METHOD} {PBO_PLAIN}"}
            for name, r in runs.items()]
        lambda_blocks.append({**rule_table(found, result["plateau_radius"]), "select": {"score": label}})
        x = runs[head]["is_score"].to_numpy() * factor
        y = runs[head]["oos_score"].to_numpy() * factor
        slope, intercept = np.polyfit(x, y, 1)
        decay_blocks.append({
            "kind": "scatter", "title": f"{label} anual — {NAME[head]} (regresión del paper)",
            "x_label": "In Sample", "y_label": "Out of Sample",
            "points": [{"x": float(a), "y": float(b), "label": str(i), "group": NAME[head]}
                       for i, (a, b) in enumerate(zip(x, y))],
            "quadrants": True,
            "fit": {"slope": float(slope), "intercept": float(intercept),
                    "r": float(np.corrcoef(x, y)[0, 1])},
            "select": {"score": label},
            "help": "Un punto por partición: el Sharpe dentro y fuera de muestra de lo que "
                    "eligió la regla, la regresión de degradación de Bailey y López de Prado. "
                    f"Anualizado ×√{PERIODS_YEAR.get(result['period'], 252.0):.0f} "
                    f"(rendimientos {PERIODO.get(result['period'], result['period'])}) solo "
                    "para leerlo: el factor no cambia ningún puesto ni el PBO.",
            "note": "Esta recta cae aunque no pase nada malo: las dos mitades son "
                    "complementarias, así que el punto elegido en cada partición se invierte "
                    "un poco por construcción — sobre ruido puro marca -0,57, y se vuelve MÁS "
                    "negativa cuanto más real es la ventaja (hasta -0,99 en una columna "
                    "genuinamente buena). Un PBO bajo junto a esta pendiente muy negativa no "
                    "es una contradicción: es la firma esperada de una selección que no está "
                    "sobreajustando. Lo que hay que leer para saber si el orden se conserva es "
                    "la «Pendiente» del veredicto y del glosario, ajustada sobre TODAS las "
                    f"variantes ({dec(result['slope'], True)} aquí), nunca el signo de esta recta."})
    return [
        envelope.tab("lambda", "Cuántas veces lo elegido queda por debajo de la mediana",
                     lambda_blocks, [selector],
                     note=f"{result['n']} variantes, {result['periods']} rendimientos "
                          f"{PERIODO.get(result['period'], result['period'])} por variante, "
                          f"{result['blocks']} bloques y "
                          f"{result['partitions']} particiones. Radio del plateau: "
                          f"{result['plateau_radius']}. El mejor dentro y el mejor "
                          f"fuera distan {result['levels_max']} niveles en el parámetro que "
                          "más se movió."),
        envelope.tab("decay", "Degradación de performance IS → OOS (regresión lineal)",
                     decay_blocks, [selector],
                     note="Este estudio no dice si la estrategia va a funcionar hacia delante: "
                          "rompe la cronología a propósito para juzgar el procedimiento de "
                          "elección. Lo que mira hacia delante es el holdout y la walk forward "
                          "matrix.")]
