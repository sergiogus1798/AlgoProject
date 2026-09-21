"""The matrix as markdown: the verdict, then what the windows allow you to claim from it."""

import pandas as pd

from strategies.walkForwardMatrix.verdict import call


def table(frame: pd.DataFrame, decimals: int = 3) -> str:
    """A frame as a markdown table.

    Args:
        frame: Any frame; the index is dropped, so name it as a column first.
        decimals: Rounding for float columns.

    Returns:
        Header, rule and one row per line. Written out rather than through
        `DataFrame.to_markdown`, which pulls in `tabulate` for one table.
    """
    shown = frame.round(decimals)
    head = "| " + " | ".join(str(c) for c in shown.columns) + " |"
    rule = "|" + "|".join("---" for _ in shown.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in row) + " |"
            for row in shown.itertuples(index=False)]
    return "\n".join([head, rule] + rows)


def preamble(result: dict) -> list[str]:
    """What the export's window geometry allows, before any number is read.

    Args:
        result: Output of `run.read`.

    Returns:
        Markdown lines.
    """
    i = result["independence"]
    return [
        "# Walk-Forward Matrix — ¿lo que optimiza bien predice lo que va bien?", "",
        f"Leído sobre `{result['metric']}` · fuente `{result['source']}`", "",
        "## Qué permite afirmar este export", "",
        f"- **{i['cells']} celdas, {i['steps_total']} tramos** sobre "
        f"{i['history_years']:.1f} años de historia.",
        f"- Dentro de una celda las ventanas de ejecución **no se solapan** "
        f"({i['oos_overlaps_within_cell']} solapes en total), así que sus tramos son "
        "observaciones separadas en el tiempo.",
        f"- Las ventanas de optimización **sí** se solapan, un "
        f"{i['is_overlap_mean']:.0%} de media entre tramos consecutivos.",
        f"- Todas las celdas reparten **la misma historia**. Por eso la unidad es la "
        f"celda, no el tramo: agrupar los {i['steps_total']} tramos en un solo ρ daría un "
        "intervalo varias veces más estrecho de lo que el dato soporta.",
        f"- Ventanas IS de {i['is_years_range'][0]:.1f} a {i['is_years_range'][1]:.1f} "
        f"años; OOS de {i['oos_years_range'][0]:.1f} a {i['oos_years_range'][1]:.1f}.",
        ""]


def verdicts(result: dict) -> list[str]:
    """One paragraph per strategy, then the supporting tables.

    Args:
        result: Output of `run.read`.

    Returns:
        Markdown lines.
    """
    lines = ["## Veredicto por estrategia", ""]
    for strategy, got in result["verdicts"].items():
        lines += [f"### {strategy}", "", call.sentence(got, result["warning"]), "",
                  f"El {got['share_negative']:.0%} de sus celdas dan ρ negativo.", ""]
    lines += ["### La misma correlación en otras métricas", "",
              "Un veredicto que solo se sostiene en la métrica con la que se leyó es una "
              "propiedad de esa métrica, no de la estrategia.", "",
              table(result["companions"]), ""]
    return lines


def drift_section(result: dict) -> list[str]:
    """How much the optimiser re-decides between steps.

    Args:
        result: Output of `run.read`.

    Returns:
        Markdown lines.
    """
    stable = result["stability"].groupby("strategy").head(3)
    return ["## Deriva del óptimo", "",
            "Cuánto cambia la tupla elegida de un tramo al siguiente. `move` está en "
            "desviaciones típicas de cada parámetro, para que un periodo y un shift sean "
            "comparables.", "",
            table(result["drift"]), "",
            "Los tres parámetros sobre los que el optimizador más se repite — candidatos "
            "a congelar en cualquier diseño:", "",
            table(stable), ""]


def matrix_section(result: dict) -> list[str]:
    """How the correlation moves along the two axes of the matrix.

    Args:
        result: Output of `run.read`.

    Returns:
        Markdown lines.
    """
    lines = ["## Los dos ejes de la matriz", ""]
    if result["warning"]:
        lines += [f"> ⚠️ {result['warning']}", ""]
    lines += ["Por número de tramos:", "", table(result["by_runs"]), "",
              "Por porcentaje fuera de muestra:", "", table(result["by_oos"]), "",
              "Cada nivel son pocas celdas y todas reparten la misma historia, así que "
              "la columna `std` describe la dispersión, **no es un error estándar**.", ""]
    return lines


def page(result: dict) -> str:
    """The whole report.

    Args:
        result: Output of `run.read`.

    Returns:
        Markdown.
    """
    return "\n".join(preamble(result) + verdicts(result)
                     + drift_section(result) + matrix_section(result))
