"""The reconnaissance as markdown: the verdict first, then what it rests on."""

import pandas as pd

VERDICT = {"proceed": "SEGUIR — el máximo supera lo que daría una rejilla de ruido",
           "noise": "RUIDO — el máximo no supera lo que daría una rejilla de ruido"}


def table(frame: pd.DataFrame, decimals: int = 4) -> str:
    """A frame as a markdown table.

    Args:
        frame: Any frame; the index is dropped, so name it as a column first.
        decimals: Rounding for float columns.

    Returns:
        Header, rule and one row per line. Written out rather than calling `to_markdown`,
        which pulls in `tabulate` -- a whole dependency pinned for one table. Copied from
        `strategies/retest/report.py`; it moves to `core/` when a third study wants it.
    """
    shown = frame.round(decimals)
    head = "| " + " | ".join(str(c) for c in shown.columns) + " |"
    rule = "|" + "|".join("---" for _ in shown.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in row) + " |"
            for row in shown.itertuples(index=False)]
    return "\n".join([head, rule] + rows)


def header(result: dict) -> list[str]:
    """The verdict and the numbers behind it.

    Args:
        result: Output of `run.read`.

    Returns:
        Markdown lines.
    """
    n, s = result["noise"], result["shape"]
    return [f"## {result['strategy']}", "",
            f"**{VERDICT[n['verdict']]}**", "",
            f"Leído sobre `{n['metric']}` · fuente `{result['source']}`", "",
            "| | |", "|---|---|",
            f"| filas de la rejilla | {n['n_rows']:,} |",
            f"| tuplas con resultado distinto (n_eff) | {n['n_eff']:,} |",
            f"| máximo observado | {n['observed_max']:.3f} |",
            f"| máximo bajo el nulo σ·√(2·ln n_eff) | {n['noise_max']:.3f} |",
            f"| cociente | **{n['ratio']:.2f}×** |",
            f"| área de meseta (> {0.0}) | {n['plateau_area']:.3f} |",
            f"| área sobre medio máximo | {n['above_half_max']:.3f} |",
            f"| (máx − mediana)/IQR | {s['spike_ratio']:.2f} |",
            f"| curtosis | {s['kurtosis']:.2f} |", ""]


def influence_table(result: dict) -> list[str]:
    """Variance explained by each parameter, on every metric read.

    Args:
        result: Output of `run.read`.

    Returns:
        Markdown lines, with the duplicate test beside it.
    """
    eta2, dup = result["eta2"], result["duplicates"]
    table_of = eta2.copy()
    table_of["grupos"] = dup["groups"]
    table_of["idénticos"] = dup["identical"]
    table_of["inerte"] = dup["inert"].map({True: "sí", False: ""})
    body = table(table_of.sort_values(result["metric"], ascending=False).reset_index())
    return ["### Influencia por parámetro", "",
            "η² es **por métrica**: el mismo parámetro puede explicar el 8 % de una y el "
            "78 % de otra, así que congelar «por η² bajo» es una elección de métrica, no "
            "una medición. El test de duplicados es independiente y ve lo que η² no ve: "
            "un parámetro que solo actúa por interacción.", "", body, ""]


def profile_tables(result: dict) -> list[str]:
    """One plateau summary per parameter.

    Args:
        result: Output of `run.read`.

    Returns:
        Markdown lines.
    """
    rows = [{"parámetro": n, **{k: v for k, v in p["plateau"].items()},
             "original": result["original"][n]}
            for n, p in result["profiles"].items()]
    return ["### Meseta y centro por parámetro", "",
            "`center` es el punto medio de la meseta contigua, no el argmax — es lo que "
            "hace el `BestValue` de SQX. Donde `center` y `argmax` se separan mucho, el "
            "pico está en el borde de lo estable.", "",
            table(pd.DataFrame(rows), decimals=2), ""]


def page(results: list[dict]) -> str:
    """The whole report.

    Args:
        results: One `run.read` output per strategy.

    Returns:
        Markdown.
    """
    lines = ["# SPP Ultra — reconocimiento", "",
             "Etapa 1 del protocolo de robustez: qué mueve el resultado, qué está muerto, "
             "y si la estrategia merece las 5.000 variantes.", "",
             "> Una tirada SPP ancha **no empareja y nunca emparejará**. Medido "
             "2026-09-19 sobre `Strategy 17.9.39`: entre la tirada IS y la OOS solo hay "
             "**6 tuplas en común de ~11.600**. Por eso nada de aquí compara dos "
             "ventanas, y por eso hacen falta las variantes.", ""]
    for result in results:
        lines += header(result) + influence_table(result) + profile_tables(result)
    return "\n".join(lines)
