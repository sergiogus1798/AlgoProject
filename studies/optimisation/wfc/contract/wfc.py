"""The walk forward correlation as the contract's blocks: the call, the cloud, its evidence."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope

STATE = {"fiable": "pass", "no_fiable": "fail", "indeciso": "watch", "sin_dato": "none"}

# The corrected sentence of encargo 24 §3 E1: encargo 22 §12.1 spoke of "924 trozos", and 924 are
# the partitions of 12 blocks, not pieces of the history.
GLOSSARY = [
    {"term": "composición",
     "text": "Qué tramos cuentan como dentro de muestra (IS) y cuáles como fuera (OOS). build va "
             "siempre dentro; dentro es build o build+oos1; fuera es lo que queda, y oos1 puede "
             "quedarse fuera de las dos. Cada composición leída se apunta en el Ledger, un "
             "renglón por tramo, y una que toque oos2 solo corre si la política lo permite."},
    {"term": "PBO y composición",
     "text": "El PBO del CSCV no cambia con la composición: parte el historial en 12 bloques y "
             "lee sus 924 particiones (C(12,6)). Solo cambian sus cuatro números cronológicos. "
             "El WFC depende entero de la composición."}]


def shown(kept: pd.DataFrame, ends: int, cols: dict) -> tuple[pd.DataFrame, int]:
    """The rows worth tabulating when the batch is too big to tabulate.

    Args:
        kept: The usable points.
        ends: How many to keep from each end of the in-sample ranking.
        cols: What `engines.variants.panel.columns` returned.

    Returns:
        The controls plus the best and worst in-sample rows, and how many were hidden. The
        question is whether the in-sample winners stayed winners, so the reader needs the
        top of the ranking and something to compare it against — not a thousand rows.
    """
    ordered = kept.sort_values(cols["is"], ascending=False)
    keep = pd.concat([ordered.head(ends), ordered.tail(ends),
                      ordered[ordered["stratum"].isin(["origin", "canary"])]])
    keep = keep[~keep.index.duplicated()].sort_values(cols["is"], ascending=False)
    return keep, len(kept) - len(keep)


def verdict(said: dict, found: dict) -> dict:
    """The call and the sentence that says what it licenses."""
    return blocks.verdict(said["call"].replace("_", " "), STATE[said["call"]], said["why"],
                          found["rho"])


def tab(kept: pd.DataFrame, found: dict, cols: dict, ends: int, note: str) -> dict:
    """The cloud of tuples, the fit through it, and the ends of the ranking as evidence."""
    x, y = kept[cols["is"]].to_numpy(float), kept[cols["oos"]].to_numpy(float)
    slope, intercept = np.polyfit(x, y, 1) if len(kept) > 1 else (0.0, 0.0)
    rows, hidden = shown(kept, ends, cols)
    lo, hi = found["ci95"]
    return envelope.tab("cloud", "¿Lo que optimiza dentro predice lo de fuera?", [
        {"kind": "scatter", "title": f"Neto {cols['is_label']} contra neto {cols['oos_label']}",
         "x_label": f"neto {cols['is_label']}", "y_label": f"neto {cols['oos_label']}",
         "points": [{"x": float(a), "y": float(b), "label": str(v), "group": str(g)}
                    for a, b, v, g in zip(x, y, kept["variant_id"], kept["stratum"])],
         "quadrants": True,
         "fit": {"slope": float(slope), "intercept": float(intercept), "r": found["pearson"]},
         "note": "Una nube que llena los cuatro cuadrantes: optimizar dentro no compra nada "
                 "fuera. Una nube sobre la diagonal ascendente: la superficie lleva "
                 "información y el ranking dentro de muestra merece confianza."},
        blocks.table("La correlación", pd.DataFrame(
            [["puntos", found["n"]], ["rho de Spearman", found["rho"]],
             ["IC 95 % desde", lo], ["IC 95 % hasta", hi], ["Pearson", found["pearson"]]],
            columns=["", "valor"])),
        blocks.table("Los extremos del ranking dentro de muestra", pd.DataFrame(
            {"variante": rows["variant_id"], "estrato": rows["stratum"],
             f"neto {cols['is_label']}": rows[cols["is"]],
             "ops dentro": rows[cols["trades_is"]],
             f"neto {cols['oos_label']}": rows[cols["oos"]],
             "ops fuera": rows[cols["trades_oos"]]}),
            f"{hidden:,} combinaciones intermedias no listadas; están todas en "
            f"metrics.parquet." if hidden else "")],
        note=note)
