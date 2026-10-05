"""The pieces every portfolio reader answers with: contract blocks, tabs, the relaxed line, the words."""

import math

# One plain sentence per figure the zone shows (owner: every statistic on screen is explained).
WORDS = {
    "score": "Puntuación por rangos: la media de los rangos de las cuatro métricas (RAR, R³, "
             "gain-to-pain, P(año perdedor)) entre todas las combinaciones medidas. 0 = la peor en "
             "todo, 1 = la mejor en todo.",
    "rar": "RAR: lo que gana al año la recta ajustada a la curva de P&L, por unidad de riesgo. "
           "Más alto, mejor.",
    "r_cubed": "R³: el RAR dividido por la caída media de las cinco mayores y por lo que duran. "
               "Premia curvas rectas con caídas cortas.",
    "gain_to_pain": "Gain-to-pain: suma de todos los meses entre la suma de los meses perdedores "
                    "(en valor absoluto). Por encima de 1 gana más de lo que sufre.",
    "p_losing_year": "P(año perdedor): la parte de los años naturales que acaban en pérdida. Más "
                     "bajo, mejor.",
    "sharpe": "Sharpe diario: media del P&L de un día entre su desviación típica. No está "
              "anualizado.",
    "floor_risk": "Riesgo mínimo: el riesgo por operación que exige el lote mínimo en la cuenta; "
                  "por debajo no se puede operar.",
    "k": "K: cuántas estrategias lleva la combinación.",
    "p95": "Percentil {q:.0f} del azar: la puntuación que solo superan {rest:.0f} de cada 100 carteras admisibles "
           "elegidas al azar del mismo tamaño. La elegida tiene que quedar por encima.",
    "p_pass": "P(pasar): de cada 100 intentos simulados del challenge, cuántos llegan al objetivo "
              "sin romper ninguna regla, dentro del plazo.",
    "D": "D: Monte Carlo de días enteros en bloques — conserva qué estrategias coinciden el mismo "
         "día.",
    "T1": "T1: Monte Carlo que baraja las operaciones de cada estrategia por separado — optimista "
          "con estrategias parecidas, porque rompe su coincidencia.",
    "T2": "T2: Monte Carlo de ventanas de historia con todas las operaciones que se abrieron en "
          "ellas — conserva qué operaciones van juntas.",
    "risk": "Riesgo por operación: fracción del saldo inicial que se arriesga en cada entrada.",
    "p_fresh": "P(pasar) repetida: la misma cifra recalculada con sorteos nuevos; si se mueve "
               "mucho, hacen falta más caminos.",
    "ev": "VE_banco: lo que se espera ganar o perder, en dólares, con toda la caja durante el "
          "horizonte simulado — cuotas pagadas, cobros, impuestos y comisiones dentro.",
    "h": "Recorte h: qué parte del edge fuera de muestra se da por perdida. h = 0 % deja el edge "
         "entero, h = 100 % lo borra.",
    "monkey": "Mono: la misma cartera sin edge (la media quitada). Es lo que sacaría la suerte "
              "sola con ese riesgo; lo que no lo supera no vale la cuota.",
    "se": "± error: el error de Monte Carlo de la cifra. Dos planes más cerca que su error no se "
          "distinguen.",
    "breakeven_h": "h de equilibrio: el recorte del edge con el que la caja deja de ganar.",
    "p_first_payout": "P(1.er cobro): probabilidad de llegar a cobrar al menos una vez.",
    "purchases": "Compras: cuántas cuentas se compran de media en el horizonte.",
    "diff": "Diferencia: Sharpe diario del método menos el de pesos iguales, en oos1. El "
            "intervalo dice entre qué valores puede estar; solo «gana» si entero queda sobre 0.",
    "band": "Banda: entre qué valores han caído los tramos de la misma duración de la propia "
            "historia de la cartera. Fuera de la banda, la lectura se marca.",
}


def clean(value: object) -> object:
    """A value JSON can carry: NaN and infinities become None, the rest is left alone."""
    return None if isinstance(value, float) and not math.isfinite(value) else value


def pct(share: float | None) -> float | None:
    """A share as a percentage with one decimal — every percentage of the zone reads alike."""
    return None if share is None or share != share else round(100 * float(share), 1)


def table(title: str, columns: list[str], rows: list[list], note: str = "",
          helps: list[str | None] | None = None, states: list[list] | None = None) -> dict:
    """A contract `table` block, compact, text columns left and figures right."""
    rows = [[clean(v) for v in r] for r in rows]
    align = ["right" if any(isinstance(r[i], (int, float)) and not isinstance(r[i], bool) for r in rows)
             else "left" for i in range(len(columns))]
    return {"kind": "table", "title": title, "columns": columns, "rows": rows, "align": align,
            "note": note, "help": helps, "states": states,
            "compact": align[-1] != "left"}       # a last column of words takes the width left


def callout(text: str, state: str = "info") -> dict:
    """A contract `callout` block."""
    return {"kind": "callout", "text": text, "state": state}


def tab(title: str, *blocks: dict, note: str = "") -> dict:
    """A contract tab holding the given blocks (None ones dropped)."""
    return {"name": title, "title": title, "note": note, "selectors": [],
            "blocks": [b for b in blocks if b]}


def headline(label: str) -> str:
    """A verdict's label as the callout prints it — «SIN VEREDICTO…» already says what it is."""
    return label if label.startswith("SIN VEREDICTO") else f"VEREDICTO: {label}"


def relaxed(marks: dict | None) -> str:
    """The line an adjusted run carries on screen; "" for a run at the owner's thresholds."""
    if not marks:
        return ""
    said = ", ".join(f"{k} = {v}" for k, v in marks.items())
    return f"AJUSTADO: umbrales relajados ({said}) — no es un resultado"


def empty(missing: str, action: str) -> dict:
    """A module with nothing to paint: what is missing and the one action that produces it."""
    return {"tabs": [], "empty": f"{missing}\n\nPara tenerlo: {action}", "relaxed": ""}
