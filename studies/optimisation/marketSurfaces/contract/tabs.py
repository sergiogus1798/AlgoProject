"""The study's numbers as the contract's tabs: the reading, the two matrices, the surfaces, the checks."""

import pandas as pd

from core.study import blocks, result

RHO_LEVELS = [-0.5, -0.3, 0.0, 0.3, 0.5, 0.7]
COSTS = ("Costes provisionales: los 9 pares y el principal se retestearon con los valores por "
         "defecto de SQX, con comisión cero. El coste por operación mueve más a las variantes que "
         "más operan, así que puede reordenar una superficie: lee esto como provisional hasta "
         "que el dueño fije los costes de The5ers.")


TERMS = {
    "Jaccard": "Solape entre las mejores combinaciones de parámetros de dos mercados: la "
               "intersección dividida por la unión de sus deciles superiores, J = |A∩B| / |A∪B|. "
               "1 = las mejores combinaciones son las mismas en los dos; 0 = ninguna en común. "
               "Por azar, con el decil, sale en torno a 0,05: lo que importa es cuánto lo supera.",
    "Jaccard por azar": "El Jaccard que darían dos órdenes de variantes independientes, y el "
                        "percentil alto de ese azar que el Jaccard observado tiene que superar.",
    "Spearman": "Correlación de rangos del Net Profit de cada variante entre el principal y "
                "este mercado: 1 = las ordenan igual, 0 = sin relación, −1 = al revés.",
    "n_eff": "Variantes con un resultado distinto en el par: dos tuplas que dan el mismo "
             "backtest cuentan una vez.",
    "exposure": "Spearman tras quitar a cada mercado lo que explica su tiempo dentro: aísla la "
                "región de parámetros de la deriva del mercado.",
    "Solape": "Cuántas variantes del decil superior comparten el principal y este mercado, "
              "sobre el tamaño del decil.",
}


def short(feed: str) -> str:
    """"EURUSD_M1" -> "EURUSD"."""
    return feed.split("_")[0]


def selector(segments: list[str]) -> dict:
    """The segment drop-down every tab shares."""
    return {"key": "segment", "label": "Tramo", "options": segments, "default": segments[0]}


def reading(rows: pd.DataFrame, segments: list[str], floor: float) -> dict:
    """The main market against each declared one: the table and the bars of rho.

    Args:
        rows: `verdict.call.against_main` with `origin_pct` added.
        segments: The segments read.
        floor: The rho floor, drawn as the bars' reference.

    Returns:
        The first tab.
    """
    out = []
    for segment in segments:
        one = rows[rows["segment"] == segment]
        table = pd.DataFrame({
            "Mercado": one["market"].map(short), "n efectivo": one["n_eff"],
            "Spearman": one["rho"], "Spearman (inf.)": one["rho_lo"],
            "Spearman (sup.)": one["rho_hi"], "Spearman sin exposición": one["rho_neutral"],
            "Jaccard": one["j"], "Jaccard por azar": one["j0"],
            "Jaccard (banda alta del azar)": one["j_hi"],
            "Solape": one["overlap"].astype(str) + "/" + one["k"].astype(str),
            "Madre (%)": one["origin_pct"], "Estado": one["state"]})
        out.append({**blocks.table(
            f"Principal contra cada mercado — {segment}", table,
            "Spearman: correlación de rangos del Net Profit entre variantes, con su intervalo "
            "al 95 %. Jaccard: solape de los deciles superiores (ver el glosario); "
            "«por azar» es lo que dan dos órdenes independientes y «banda alta» su percentil "
            "alto. Madre: dónde cae la madre en ese mercado (100 = la mejor). «Sin exposición»: "
            "el mismo Spearman quitando a cada mercado lo que explica su tiempo dentro — en "
            "estrategias sólo largas, parte del orden es exposición por deriva del mercado, no "
            "región de parámetros."),
            "help": [None, TERMS["n_eff"], TERMS["Spearman"], None, None, TERMS["exposure"],
                     TERMS["Jaccard"], TERMS["Jaccard por azar"], TERMS["Jaccard por azar"],
                     TERMS["Solape"], None, None],
            "select": {"segment": segment}})
        out.append({"kind": "bars", "title": f"Spearman con el principal — {segment}", "unit": "",
                    "items": [{"label": short(m), "value": r, "error": [lo, hi], "state": s}
                              for m, r, lo, hi, s in zip(one["market"], one["rho"],
                                                         one["rho_lo"], one["rho_hi"],
                                                         one["state"])],
                    "reference": floor, "select": {"segment": segment}})
    return result.tab("lectura", "La lectura", out, [selector(segments)],
                      "¿La región buena de parámetros en el mercado principal es también la "
                      "buena en los otros? " + COSTS)


def matrices(pairs: pd.DataFrame, segments: list[str], order: list[str]) -> dict:
    """rho_ab and J_ab between every pair of markets, one grid each per segment.

    Args:
        pairs: `measure.pairs.matrix` of every segment, with a `segment` column.
        segments: The segments read.
        order: Market order, the main one first.

    Returns:
        The second tab.
    """
    names = [short(m) for m in order]
    out = []
    for segment in segments:
        one = pairs[pairs["segment"] == segment]
        both = pd.concat([one, one.rename(columns={"a": "b", "b": "a"})]).drop_duplicates(["a", "b"])
        for key, title, levels in (("rho", "Spearman", RHO_LEVELS),
                                   ("j", "Jaccard del decil superior", None)):
            grid = both.pivot(index="a", columns="b", values=key).reindex(index=order, columns=order)
            j0 = float(one["j0"].median())
            out.append({"kind": "grid", "title": f"{title} — {segment}", "rows": names,
                        "cols": names, "values": grid.to_numpy().tolist(),
                        "scale": "discrete",
                        "levels": levels or [round(j0, 3), round(2 * j0, 3), 0.2, 0.3, 0.5],
                        "labels": None, "select": {"segment": segment}})
    return result.tab("matrices", "Todos los pares", out, [selector(segments)],
                      "Cada casilla compara dos mercados sobre las mismas variantes. La "
                      "diagonal es 1 por construcción: es el control de que las variantes se "
                      "emparejaron por su identificador.")


def checks(found: pd.DataFrame, diagonal: pd.DataFrame, agrees: float) -> dict:
    """The three verifications of §3 of the encargo.

    Args:
        found: `measure.verify.markets` and `measure.verify.main`, concatenated.
        diagonal: `measure.verify.diagonal`.
        agrees: The rank agreement a curve must reach.

    Returns:
        The fourth tab.
    """
    table = found.assign(market=found["market"].map(short)).rename(columns={
        "check": "Comprobación", "market": "Mercado", "segment": "Tramo", "n": "n",
        "rho": "Spearman", "rho_wrong": "Spearman (mercado equivocado)",
        "within_1usd": "Dentro de 1 USD", "gap_median": "Diferencia mediana",
        "gap_max": "Diferencia máxima"})
    diag = diagonal.assign(a=diagonal["a"].map(short)).rename(columns={
        "segment": "Tramo", "a": "Mercado", "rho": "Spearman", "j": "Jaccard"})
    return result.tab("verificacion", "Verificación", [
        blocks.table("La superficie sale del resultado correcto", table,
                     f"Spearman: orden de la curva diaria sumada contra el Net Profit de SQX; "
                     f"tiene que pasar de {agrees}. «Mercado equivocado»: la misma curva contra "
                     f"el mercado siguiente, que es lo que daría un emparejamiento erróneo. Los "
                     f"dólares no tienen por qué cuadrar (ver «Dentro de 1 USD»)."),
        blocks.table("Spearman y Jaccard de cada mercado consigo mismo", diag,
                     "Tienen que ser exactamente 1: si no, las variantes no se emparejaron "
                     "por identidad.")])
