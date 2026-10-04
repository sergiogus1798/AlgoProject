"""The walk forward correlation as the contract's blocks: the cloud, its evidence, its strata."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope

LABEL = {"fiable": "Fiable", "no_fiable": "No fiable", "indeciso": "Indeciso",
         "sin_dato": "Sin dato"}
GROUP = {"origin": "Original", "canary": "Control", "neighbourhood": "Vecindad",
         "factorial": "Factorial", "coverage": "Cobertura"}
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
    {"term": "Operar poco",
     "text": "Una combinación se descarta si en el tramo dentro de muestra (IS) o en el de fuera "
             "(OOS) hizo menos operaciones que el mínimo configurado (min_trades). Con tan pocas "
             "operaciones su beneficio mide un par de trades, no la superficie de parámetros."},
    {"term": "Ratio OOS/IS",
     "text": "Sharpe fuera de muestra dividido por el Sharpe dentro, variante a variante. Por "
             "debajo de 1, la variante rinde menos fuera que dentro (decaimiento); por encima, "
             "igual o más. Se calcula solo donde el Sharpe IS supera un suelo positivo pequeño: "
             "con un denominador cercano a cero o negativo el cociente se dispara y no significa "
             "nada. Nunca se promedian ratios: se mira la distribución y su mediana."}]

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
    pct = f"{found['rho'] * 100:.2f}".replace(".", ",")
    label = LABEL[said["call"]]
    # The percentage is the verdict card's big score, beside the label (owner, 2026-10-04).
    score = None if said["call"] == "sin_dato" else f"Spearman {pct} %"
    return blocks.verdict(label, STATE[said["call"]], said["why"], score)


def slope(kept: pd.DataFrame, cols: dict) -> float:
    """Least-squares slope of out-of-sample net profit on in-sample net profit."""
    if len(kept) < 2:
        return float("nan")
    return float(np.polyfit(kept[cols["is"]].to_numpy(float), kept[cols["oos"]].to_numpy(float),
                            1)[0])


def decay(kept: pd.DataFrame, cols: dict, tag: dict, floor: float) -> list[dict]:
    """The per-variant Sharpe ratio OOS/IS and the IS and OOS Sharpe distributions overlaid.

    Args:
        kept: The usable points under this composition.
        cols: What `engines.variants.panel.columns` returned.
        tag: The selector tag of this partition.
        floor: Only variants whose IS Sharpe is above this enter the ratio.

    Returns:
        A ratio histogram (median marked, never averaged) with the count of variants left out
        in its note, and the IS/OOS overlay. Empty when the batch has no Sharpe columns.
    """
    ci, co = f"SharpeRatio ({cols['is_label']})", f"SharpeRatio ({cols['oos_label']})"
    if ci not in kept or co not in kept:
        return []
    sub = kept[[ci, co]].dropna()
    a, b = sub[ci].to_numpy(float), sub[co].to_numpy(float)
    ok = a > floor
    out = []
    if ok.sum() >= 5:
        hist = blocks.distribution(
            "Ratio Sharpe OOS/IS por variante", "", b[ok] / a[ok], 1.0,
            f"{int((~ok).sum())} de {len(kept)} variantes quedan fuera por tener un Sharpe IS "
            f"de {floor:g} o menos (o sin Sharpe): con un IS cercano a cero o negativo el "
            "cociente se dispara. Rojo: la variante rinde menos fuera que dentro (ratio por debajo "
            "de 1); verde: igual o más. La línea discontinua es la mediana. Es solo una lectura "
            "visual, no un criterio.", pivot=1.0)
        hist["band"] = [None, None]   # the 5-95 band would hide the red/green shading at 1
        out.append({**hist, "mark": "Paridad OOS = IS", **tag})
    out.append({**blocks.distribution(
        "Sharpe IS y OOS superpuestos", "", np.concatenate([a, b]), None,
        "IS y OOS solapadas como densidad (cada una integra a 1): compara su forma, no el "
        "tamaño de la muestra.", series={"IS": a, "OOS": b}), **tag})
    return out


def partition(kept: pd.DataFrame, found: dict, said: dict, cols: dict, name: str,
             dropped: int, total: int, floor: float, min_trades: int,
             sharpe_floor: float) -> list[dict]:
    """One composition's blocks: top line, scatter, decay figures — tagged for the selector.

    Args:
        kept: The usable points under this composition.
        found: What `measure.correlation.correlation` returned.
        said: What `measure.correlation.verdict` returned.
        cols: What `engines.variants.panel.columns` returned for this composition.
        name: The composition's label (`panel.label`), the selector's option value.
        dropped: Combinations discarded by the trade floor under this composition.
        total: Combinations fabricated in the batch, before any floor.
        floor: The rho floor this composition's verdict was judged against.
        min_trades: The trade floor behind «operar poco».
        sharpe_floor: The IS Sharpe above which a variant enters the OOS/IS ratio.

    Returns:
        Blocks all tagged `"select": {"partición": name}` — the top line, the scatter, the
        decay histograms and, only when the call is `no_fiable`, a highlighted callout.
    """
    tag = {"select": {"partición": name}}
    x, y = kept[cols["is"]].to_numpy(float), kept[cols["oos"]].to_numpy(float)
    m = slope(kept, cols)
    b = np.polyfit(x, y, 1)[1] if len(kept) > 1 else 0.0
    out = [
        {"kind": "callout", "state": "info", **tag,
         "text": f"{total} combinaciones medidas · {dropped} descartadas por operar poco en esta "
                 f"partición (menos de {min_trades} operaciones en el tramo IS o en el OOS) · "
                 f"{len(kept)} usadas."},
        {"kind": "scatter", "title": f"{cols['is_label']} (dentro de muestra) contra "
         f"{cols['oos_label']} (fuera de muestra)", **tag,
         "x_label": f"{cols['is_label']} — dentro de muestra", "y_label":
         f"{cols['oos_label']} — fuera de muestra",
         "points": [{"x": float(a), "y": float(c), "label": str(v),
                    "group": GROUP.get(str(g), str(g))}
                    for a, c, v, g in zip(x, y, kept["variant_id"], kept["stratum"])],
         "quadrants": True,
         "fit": {"slope": float(m), "intercept": float(b), "r": found["pearson"]},
         "note": "Una nube que llena los cuatro cuadrantes: optimizar dentro no compra nada "
                 "fuera. Una nube sobre la diagonal ascendente: la superficie lleva "
                 "información y el ranking dentro de muestra merece confianza. Colores: Original es la "
                 "tupla sin mover; Control, variantes de resultado conocido para detectar una "
                 "cadena rota; Vecindad, a pocos pasos de la original; Factorial, rejilla "
                 "completa sobre unos pocos niveles; Cobertura, barrido de todo el espacio."},
        *decay(kept, cols, tag, sharpe_floor)]
    if said["call"] == "no_fiable":
        out.append({"kind": "callout", "state": "fail", **tag,
                    "text": NO_FIABLE.format(rho=found["rho"], floor=floor)})
    return out


def correlations(parts: list) -> dict:
    """One row per partition: points, Spearman, Pearson and slope (feedback 16)."""
    rows = [[n, found["n"], found["rho"], found["pearson"], slope(kept, cols)]
            for n, kept, found, _, cols, _, _ in parts]
    return blocks.table(
        "Correlaciones por partición", pd.DataFrame(
            rows, columns=["Partición", "Puntos", "Spearman", "Pearson", "Pendiente"]),
        "Spearman: correlación de rangos, robusta a un punto suelto. Pearson: lineal, sensible a "
        "la escala. Pendiente: mínimos cuadrados del beneficio neto OOS sobre el IS.", digits=3)


def tab(parts: list[tuple[str, pd.DataFrame, dict, dict, dict, int, int]], default: str,
       floor: float, note: str, min_trades: int, sharpe_floor: float) -> dict:
    """The whole tab: every composition's blocks, one selector switching between them.

    Args:
        parts: One (name, kept, found, said, cols, dropped, total) tuple per composition
            offered by `engines.variants.look.offered` — every partition the ledger's door
            allows on this asset today.
        default: The composition this run was launched with; the selector's starting value.
        floor: The rho floor every composition's verdict was judged against.
        note: The paragraph the tab opens with.
        min_trades: The trade floor, quoted in the «operar poco» line.
        sharpe_floor: The IS Sharpe floor of the OOS/IS ratio histogram.

    Returns:
        A tab whose blocks the window filters and redraws without calling the study again
        (CONTRACT §1): switching the selector recomputes nothing on the Python side because
        every partition already sits in the result.
    """
    names = [p[0] for p in parts]
    strata = {"kind": "list", "title": "Qué es cada estrato de la nube", "note": None,
             "items": STRATA_ITEMS}
    blocks_ = [b for name, kept, found, said, cols, dropped, total in parts
              for b in partition(kept, found, said, cols, name, dropped, total, floor,
                              min_trades, sharpe_floor)]
    return envelope.tab("cloud", "¿Lo que optimiza dentro predice lo de fuera?",
                        blocks_ + [correlations(parts), strata],
                        selectors=[{"key": "partición", "label": "Partición", "options": names,
                                    "default": default}],
                        note=note)
