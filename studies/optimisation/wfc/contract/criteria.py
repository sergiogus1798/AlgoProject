"""The WFC's criteria metrics as two tables of the tab and as the fields of the result's summary."""

import pandas as pd

from core.study import blocks

TITLE = "Métricas para criterios — sin umbral todavía"
NULL = ("Lo que daría esta misma familia sin ventaja fuera de muestra: el beneficio de cada día "
        "OOS se multiplica por +1 o −1 al azar, el mismo signo para todas las variantes, así "
        "cada una espera cero y siguen pareciéndose entre sí igual que antes. Percentiles 5 a "
        "95 de 1.000 sorteos. Si el valor real cae dentro, no se distingue de no tener ventaja.")


def es(value: float | None, pattern: str = "{:.2f}") -> str:
    """A number as the panel prints it, decimal comma; «—» for a missing one."""
    return "—" if value is None else pattern.format(value).replace(".", ",")


def span(levels: list | None, pattern: str) -> str:
    """A null's 5th to 95th percentile as «lo a hi»."""
    return "—" if levels is None else f"{es(levels[0], pattern)} a {es(levels[-1], pattern)}"


def summary(windows: dict[str, dict], asked: dict) -> dict:
    """The flat fields the databank table and the autopilot read (`wfc.summary.<field>`).

    Args:
        windows: Out-of-sample segment → `persistence.measure` of build against it alone.
        asked: `persistence.measure` of the composition this run was launched with.

    Returns:
        `exceso_persistencia_<segment>` per window, `exceso_persistencia_minimo` (the worst
        window: «holds in every window» is a threshold on it) and `mediana_ratio_Sharpe`.
    """
    out = {f"exceso_persistencia_{seg}": m["excess"] for seg, m in windows.items()}
    return out | {"exceso_persistencia_minimo": min(m["excess"] for m in windows.values()),
                  "mediana_ratio_Sharpe": asked["ratio"]}


def tables(windows: dict[str, dict], parts: dict[str, dict], top: float, keep: float) -> list[dict]:
    """The two tables: the top's persistence per out-of-sample window, the ratio per partition.

    Cells are text on purpose: the autopilot reads these numbers from the summary, and a
    numeric cell here would offer each of them a second time under the table's name.

    Args:
        windows: Out-of-sample segment → its measure, build in sample.
        parts: Partition label → its measure.
        top, keep: The two shares of the persistence, quoted in the headers' tooltips.
    """
    rows = [[seg.upper(), str(m["n"]), es(100 * m["share"], "{:.1f} %"), es(100 * m["baseline"], "{:.0f} %"),
             es(100 * m["excess"], "{:+.1f} pp"), span([100 * x for x in m["null"]["excess"]],
                                                       "{:+.0f} pp")]
            for seg, m in windows.items()]
    worst = min(windows.values(), key=lambda m: m["excess"])
    rows.append(["Peor ventana", "", es(100 * worst["share"], "{:.1f} %"), "",
                 es(100 * worst["excess"], "{:+.1f} pp"), ""])
    persist = blocks.table(
        f"{TITLE}: persistencia del top", pd.DataFrame(rows, columns=[
            "Ventana OOS", "Variantes", "Persistencia", "Por azar", "Exceso",
            "Exceso sin ventaja"]),
        f"De las variantes en el mejor {top:.0%} del build por Net Profit, cuántas quedan en el "
        f"mejor {keep:.0%} de cada ventana fuera de muestra. «Se cumple en todas» es mirar la "
        "peor ventana. Solo aparecen las ventanas que el ledger deja leer hoy.") | {
        "compact": True, "help": [
            None, "Variantes con operaciones suficientes en el build y en esa ventana.",
            f"Porcentaje del mejor {top:.0%} dentro de muestra (build, por Net Profit) que queda "
            f"en el mejor {keep:.0%} de la ventana.",
            f"Lo que saldría sin ninguna relación entre los dos rankings: {keep:.0%}, por "
            "construcción. Un top siempre «persiste» en esa medida aunque no haya nada.",
            "Persistencia menos su valor por azar, en puntos porcentuales: lo que el ranking "
            "dentro de muestra aporta de verdad. Es el dato que se ofrece como criterio.", NULL]}
    rows = [[name, f"{m['n_ratio']} de {m['n']}", es(m["ratio"]), span(m["null"]["ratio"], "{:.2f}")]
            for name, m in parts.items()]
    decay = blocks.table(
        f"{TITLE}: mediana del ratio Sharpe OOS/IS", pd.DataFrame(rows, columns=[
            "Partición", "Variantes en el ratio", "Mediana del ratio", "Mediana sin ventaja"]),
        "Diagnóstico, no criterio: con un solo camino de precios fuera de muestra el rango sin "
        "ventaja cubre casi siempre el valor real.") | {
        "compact": True, "help": [
            None, "Solo entran las variantes cuyo Sharpe dentro de muestra supera el suelo "
                  "(sharpe_floor): con un denominador cercano a cero el cociente se dispara.",
            "Mediana, variante a variante, del Sharpe OOS entre el Sharpe IS: una mediana de "
            "ratios, no un cociente de medianas. Los dos Sharpe son los anualizados de SQX "
            "(√252), comparables entre tramos de distinta duración. Entrar por tener un Sharpe "
            "IS alto regresa a la media por sí solo: sin decaimiento alguno queda algo por "
            "debajo de 1.", NULL]}
    return [persist, decay]
