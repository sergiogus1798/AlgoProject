"""The surfaces' criteria metrics as tables of the reading tab and as the summary's flat fields."""

import numpy as np
import pandas as pd

from core.study import blocks
from studies.optimisation.marketSurfaces.contract.tabs import short
from studies.optimisation.marketSurfaces.measure import lift

TITLE = "Métricas para criterios — sin umbral todavía"
NULL = ("«Sin ventaja» es este mismo mercado con el signo del beneficio de cada día sorteado, "
        "el mismo signo para todas las variantes, mil veces: cada variante espera cero y las "
        "variantes siguen pareciéndose entre sí como antes. Por eso su rango es más ancho que "
        "el del azar de variantes independientes (q/(2−q)).")
HELP = [
    None,
    "Solape del decil superior del principal con el de este mercado, J = |A∩B| / |A∪B|.",
    "El Jaccard medio que da este mercado sin ventaja contra el decil real del principal. "
    + NULL,
    "Lift = Jaccard / Jaccard por azar. 1 = el solape que habría sin ventaja; 2 = el doble. "
    "No es un pasa/no pasa: es una puntuación. Ojo: en estrategias solo largas, dos mercados "
    "que suben a la vez ordenan las variantes por tiempo dentro, y eso también sube el lift "
    "sin que la región de parámetros viaje (mira «Spearman sin exposición»).",
    "Entre qué valores cae el lift del 90 % central de los sorteos sin ventaja. Un lift "
    "dentro de este rango no se distingue de un mercado sin ventaja.",
    "Si la madre (el punto elegido, θ₀) está en el decil superior de las variantes de este "
    "mercado.",
    "En qué porcentaje de los sorteos sin ventaja la madre cae en ese decil: no es un 10 % "
    "exacto, porque una variante que opera más tiene más varianza y entra más veces en los "
    "dos extremos."]
NOTE = ("Calculadas y visibles, sin juzgar: ninguna tiene umbral ni cambia la lectura. "
        f"Un mercado con menos de {lift.MIN_VARIANTS} variantes utilizables en común con el "
        "principal no aparece: su dato falta, no es un cero. «Todos»: la mediana del lift "
        "entre mercados y el porcentaje de mercados con la madre en su decil superior, con "
        "su exceso sobre lo que saldría sin ventaja — los sorteos son los mismos días para "
        "todos los mercados, así que cuentan lo correlacionados que están.")


def es(value: float | None, pattern: str = "{:.2f}") -> str:
    """A number as the panel prints it, decimal comma; «—» for a missing one."""
    return "—" if value is None else pattern.format(value).replace(".", ",")


def span(levels: list | None, pattern: str = "{:.2f}") -> str:
    """A null's 5th to 95th percentile as «lo a hi»."""
    return "—" if levels is None else f"{es(levels[0], pattern)} a {es(levels[-1], pattern)}"


def table(segment: str, found: dict) -> dict:
    """One segment's markets, and the row that reads them together. Cells are text: the
    facts are the summary's fields, and a number here would only repeat them."""
    rows = [[short(m), es(d["j"], "{:.3f}"), es(d["chance"], "{:.3f}"), es(d["lift"]),
             span(None if d["lifts"] is None else np.percentile(d["lifts"], [5, 95])),
             "—" if d["inside"] is None else ("sí" if d["inside"] else "no"),
             "—" if d["inside_null"] is None else es(100 * d["inside_null"].mean(), "{:.0f} %")]
            for m, d in found["markets"].items()]
    a = found["all"]
    inside = "—" if a["inside"] is None else (
        f"{es(100 * a['inside'], '{:.0f} %')} (exceso {es(100 * a['excess'], '{:+.0f} pp')}; sin "
        f"ventaja {span([100 * v for v in a['null']['excess']], '{:+.0f} pp')})")
    rows.append([f"Todos ({a['markets']})", "", "", es(a["lift"]), span(a["null"]["lift"]),
                 inside, "—" if a["baseline"] is None else es(100 * a["baseline"], "{:.0f} %")])
    return blocks.table(
        f"{TITLE}: lift del Jaccard y la madre en el decil de cada mercado — {segment}",
        pd.DataFrame(rows, columns=["Mercado", "Jaccard", "Jaccard por azar", "Lift",
                                    "Lift sin ventaja", "Madre en el decil superior",
                                    "Por azar"]), NOTE) | {
        "help": HELP, "compact": True, "select": {"segment": segment}}


def into(tab: dict, lifts: dict) -> dict:
    """The reading tab with each segment's criteria table after its own blocks."""
    tab["blocks"] += [table(segment, found) for segment, found in lifts.items()]
    return tab


def summary(lifts: dict) -> dict:
    """The flat fields the databank table and the autopilot read (`marketSurfaces.summary.*`)."""
    out = {}
    for segment, found in lifts.items():
        out[f"lift_Jaccard_mediano_{segment}"] = found["all"]["lift"]
        out[f"exceso_madre_en_top_{segment}"] = found["all"]["excess"]
    return out
