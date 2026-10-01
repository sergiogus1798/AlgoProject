"""The study's numbers as the contract's tabs: the reading, the two matrices, the surfaces, the checks."""

import pandas as pd

from core.study import blocks, result

RHO_LEVELS = [-0.5, -0.3, 0.0, 0.3, 0.5, 0.7]
COSTS = ("Costes PROVISIONALES: los 9 pares y el principal se retestearon con los defaults de "
         "fábrica de SQX, comisión CERO. El coste por operación mueve más a las variantes que "
         "más operan, así que puede reordenar una superficie: lee esto como provisional hasta "
         "que el dueño fije los costes de the5ers.")


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
            "mercado": one["market"].map(short), "n_eff": one["n_eff"], "rho": one["rho"],
            "rho_lo": one["rho_lo"], "rho_hi": one["rho_hi"],
            "rho_sin_exp": one["rho_neutral"], "J": one["j"],
            "J_azar": one["j0"], "J_banda": one["j_hi"],
            "solape": one["overlap"].astype(str) + "/" + one["k"].astype(str),
            "madre_pct": one["origin_pct"], "estado": one["state"]})
        out.append({**blocks.table(
            f"Principal contra cada mercado — {segment}", table,
            "rho: Spearman del beneficio neto entre variantes, con su intervalo al 95 %. J: "
            "Jaccard de los deciles superiores; J_azar es lo que dan dos órdenes "
            "independientes y J_banda su percentil alto. madre_pct: dónde cae la madre en "
            "ese mercado (100 = la mejor). rho_sin_exp: el mismo rho quitando a cada "
            "mercado lo que explica su tiempo dentro — en estrategias sólo largas, parte del "
            "orden es exposición por deriva del mercado, no región de parámetros."),
            "select": {"segment": segment}})
        out.append({"kind": "bars", "title": f"rho con el principal — {segment}", "unit": "",
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
        for key, title, levels in (("rho", "rho de Spearman", RHO_LEVELS),
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


def surfaces(cells: pd.DataFrame, segments: list[str], order: list[str],
             origin: str) -> dict:
    """One surface per market and segment: the spread of the metric with the mother marked.

    Args:
        cells: `inputs.surfaces.long`, only usable cells.
        segments: The segments read.
        order: Market order, the main one first.
        origin: The mother's `variant_id`.

    Returns:
        The third tab, a distribution per (market, segment).
    """
    out = []
    for market in order:
        for segment in segments:
            one = cells[(cells["market"] == market) & (cells["segment"] == segment)]
            mother = one.loc[one["variant_id"] == origin, "value"]
            block = blocks.distribution(
                f"{short(market)} — {segment}", "USD", one["value"].to_numpy(),
                float(mother.iloc[0]) if len(mother) else float("nan"),
                "Beneficio neto de cada variante en este mercado y tramo; la línea es la madre.")
            out.append({**block, "mark": "madre", "select": {"market": short(market),
                                                              "segment": segment}})
    markets = {"key": "market", "label": "Mercado", "options": [short(m) for m in order],
               "default": short(order[0])}
    return result.tab("superficies", "Una superficie por mercado", out,
                      [markets, selector(segments)],
                      "La superficie es el beneficio neto de las variantes en un mercado. "
                      "Su nivel depende del coste (provisional); lo que se compara entre "
                      "mercados es el orden, no el nivel.")


def checks(found: pd.DataFrame, diagonal: pd.DataFrame, agrees: float) -> dict:
    """The three verifications of §3 of the encargo.

    Args:
        found: `measure.verify.markets` and `measure.verify.main`, concatenated.
        diagonal: `measure.verify.diagonal`.
        agrees: The rank agreement a curve must reach.

    Returns:
        The fourth tab.
    """
    table = found.assign(market=found["market"].map(short))
    diag = diagonal.assign(a=diagonal["a"].map(short))
    return result.tab("verificacion", "Verificación", [
        blocks.table("La superficie sale del resultado correcto", table,
                     f"rho: orden de la curva diaria sumada contra el beneficio de SQX; tiene "
                     f"que pasar de {agrees}. rho_wrong: la misma curva contra el mercado "
                     f"siguiente, que es lo que daría un emparejamiento equivocado. Los "
                     f"dólares no tienen por qué cuadrar (ver within_1usd)."),
        blocks.table("rho de cada mercado consigo mismo", diag,
                     "Tiene que ser exactamente 1: si no, las variantes no se emparejaron "
                     "por identidad.")])
