"""The walk forward correlation as the contract's blocks: the cloud, its evidence, its strata."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope

STATE = {"fiable": "pass", "no_fiable": "fail", "indeciso": "watch", "sin_dato": "none"}

# The corrected sentence of encargo 24 §3 E1: the CSCV's count is of partitions, not pieces of
# the history — C(16,8) = 12,870 since the owner's 16 blocks (2026-09-30).
GLOSSARY = [
    {"term": "composición",
     "text": "Qué tramos cuentan como dentro de muestra (IS) y cuáles como fuera (OOS). build va "
             "siempre dentro; dentro es build o build+oos1; fuera es lo que queda, y oos1 puede "
             "quedarse fuera de las dos. Cada composición leída se apunta en el Ledger, un "
             "renglón por tramo, y una que toque oos2 solo corre si la política lo permite."},
    {"term": "PBO y composición",
     "text": "El PBO del CSCV no cambia con la composición: parte el historial en 16 bloques y "
             "lee sus 12.870 particiones (C(16,8)). Solo cambian sus cuatro números cronológicos. "
             "El WFC depende entero de la composición."},
    {"term": "IC 95 % de la correlación",
     "text": "Intervalo de Fisher-z, no bootstrap: transforma rho, calcula el margen sobre "
             "1/√(n-3) y deshace la transformación. Asume que los puntos son independientes; "
             "aquí no lo son del todo — combinaciones vecinas del grid comparten parámetros y "
             "se mueven juntas — así que el intervalo real es algo más ancho que el mostrado."}]

# What each stratum of the design contributes (feedback §10.8): read together with
# `sqx/variants/design/strata.py` and `canaries.py`, which this only paraphrases for the reader.

STRATA_ITEMS = [
    {"title": "Origin", "text": "La tupla original, sin parámetros movidos."},
    {"title": "Canary", "text": "Controles de resultado ya conocido — detectan una cadena rota, "
                                "no leen la superficie."},
    {"title": "Neighborhood", "text": "A pocos pasos de nivel del punto elegido: qué tan "
                                      "empinada es la meseta ahí mismo."},
    {"title": "Factorial", "text": "Rejilla completa sobre un subconjunto de niveles: hace "
                                   "visible una interacción entre dos parámetros."},
    {"title": "Coverage", "text": "Barrido de baja discrepancia de todo el espacio, parámetros "
                                  "congelados incluidos: llega a las esquinas."}]

NO_FIABLE = ("Optimizar en IS no predice fuera: correlación de {rho:.2f}, por debajo de "
             "{floor:.2f}.")


def verdict(said: dict, found: dict) -> dict:
    """The call and the sentence that says what it licenses."""
    return blocks.verdict(said["call"].replace("_", " "), STATE[said["call"]], said["why"],
                          found["rho"])


def partition(kept: pd.DataFrame, found: dict, said: dict, cols: dict, name: str,
             dropped: int, total: int, floor: float) -> list[dict]:
    """One composition's blocks: top line, scatter, correlation table — tagged for the selector.

    Args:
        kept: The usable points under this composition.
        found: What `measure.correlation.correlation` returned.
        said: What `measure.correlation.verdict` returned.
        cols: What `engines.variants.panel.columns` returned for this composition.
        name: The composition's label (`panel.label`), the selector's option value.
        dropped: Combinations discarded by the trade floor under this composition.
        total: Combinations fabricated in the batch, before any floor.
        floor: The rho floor this composition's verdict was judged against.

    Returns:
        Blocks all tagged `"select": {"partición": name}` — the top line, the scatter, the
        correlation table and, only when the call is `no_fiable`, a highlighted callout
        (feedback §8.2: no "falla/nota/error/intervalo", a plain warning sentence instead).
    """
    tag = {"select": {"partición": name}}
    x, y = kept[cols["is"]].to_numpy(float), kept[cols["oos"]].to_numpy(float)
    slope, intercept = np.polyfit(x, y, 1) if len(kept) > 1 else (0.0, 0.0)
    lo, hi = found["ci95"]
    out = [
        {"kind": "callout", "state": "info", **tag,
         "text": f"{total} combinaciones fabricadas · {dropped} descartadas por operar poco · "
                 f"{len(kept)} usadas."},
        {"kind": "scatter", "title": f"{cols['is_label']} (In Sample) contra "
         f"{cols['oos_label']} (Out of Sample)", **tag,
         "x_label": f"{cols['is_label']} — In Sample", "y_label":
         f"{cols['oos_label']} — Out of Sample",
         "points": [{"x": float(a), "y": float(b), "label": str(v), "group": str(g)}
                    for a, b, v, g in zip(x, y, kept["variant_id"], kept["stratum"])],
         "quadrants": True,
         "fit": {"slope": float(slope), "intercept": float(intercept), "r": found["pearson"]},
         "note": "Una nube que llena los cuatro cuadrantes: optimizar dentro no compra nada "
                 "fuera. Una nube sobre la diagonal ascendente: la superficie lleva "
                 "información y el ranking dentro de muestra merece confianza."},
        {**blocks.table("La correlación", pd.DataFrame(
            [["puntos", found["n"]],
             ["Correlación de Spearman (rango, robusta a un punto suelto)", found["rho"]],
             ["Correlación de Pearson (lineal, sensible a la escala)", found["pearson"]],
             ["pendiente IS→OOS (mínimos cuadrados sobre estos puntos)", slope],
             ["IC 95 % desde", lo], ["IC 95 % hasta", hi]],
            columns=["", "valor"])),
         "help": ["El intervalo de confianza asume independencia entre puntos; ver "
                  "glosario.", None], **tag}]
    if said["call"] == "no_fiable":
        out.append({"kind": "callout", "state": "fail", **tag,
                    "text": NO_FIABLE.format(rho=found["rho"], floor=floor)})
    return out


def tab(parts: list[tuple[str, pd.DataFrame, dict, dict, dict, int, int]], default: str,
       floor: float, note: str) -> dict:
    """The whole tab: every composition's blocks, one selector switching between them.

    Args:
        parts: One (name, kept, found, said, cols, dropped, total) tuple per composition
            offered by `engines.variants.look.offered` — every partition the ledger's door
            allows on this asset today.
        default: The composition this run was launched with; the selector's starting value.
        floor: The rho floor every composition's verdict was judged against.
        note: The paragraph the tab opens with.

    Returns:
        A tab whose blocks the window filters and redraws without calling the study again
        (CONTRACT §1): switching the selector recomputes nothing on the Python side because
        every partition already sits in the result.
    """
    names = [p[0] for p in parts]
    strata = {"kind": "list", "title": "Qué es cada estrato de la nube", "note": None,
             "items": STRATA_ITEMS}
    blocks_ = [b for name, kept, found, said, cols, dropped, total in parts
              for b in partition(kept, found, said, cols, name, dropped, total, floor)]
    return envelope.tab("cloud", "¿Lo que optimiza dentro predice lo de fuera?",
                        blocks_ + [strata],
                        selectors=[{"key": "partición", "label": "Partición", "options": names,
                                    "default": default}],
                        note=note)
