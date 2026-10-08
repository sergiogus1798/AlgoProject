"""Step 17 as the contract's blocks: the call, the three compositions, the cloud and the filters."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from engines.variants import panel
from studies.optimisation.wfc.contract import words as w


def es(value: float, pattern: str = "{:.2f}") -> str:
    """A number inside a sentence, decimal comma."""
    return pattern.format(value).replace(".", ",")


def verdict(facts: dict, need: int, level_alpha: float) -> dict:
    """The deciding composition's state and the sentence of its cell of the owner's table."""
    order, said = facts["orden"], facts["estado"]
    if order == "sin_dato":
        return blocks.verdict(w.LABEL[said], w.STATE[said], w.NO_DATA.format(need=need))
    wins = facts["nivel_top"] > 0
    unbeaten = wins and facts["p_nivel"] > level_alpha
    meaning = w.MEANING[order, wins] + (w.NOT_BEATEN.format(
        p=es(facts["p_nivel"], "{:.3f}"), alpha=es(level_alpha)) if unbeaten else w.VETO)
    return blocks.verdict(w.LABEL[said], w.STATE[said], meaning, f"ρ {es(facts['rho'])}")


def name(key: str) -> str:
    """A composition as the reader sees it: «c1 · build+oos1 → oos2»."""
    cols = panel.columns(panel.KEYS[key])
    return f"{key} · {cols['is_label']} → {cols['oos_label']}"


def compositions(measured: dict[str, dict]) -> dict:
    """One row per composition: the order with its null, the level, and the state of the one that decides."""
    rows = []
    for key, got in measured.items():
        f, cols = got["facts"], panel.columns(panel.KEYS[key])
        order = w.ORDER[f["orden"]] + (" (fuerte)" if f.get("fuerte") else "")
        rows.append([key, cols["is_label"], cols["oos_label"], f["n"], f.get("rho"),
                     f.get("p_mas"), f.get("p_menos"), f.get("nulo_p5"), f.get("nulo_p95"),
                     order, f.get("n_top"), f.get("nivel_top"), f.get("p_nivel"),
                     f.get("nivel_todas"),
                     f.get("r_sel"), w.LABEL[f["estado"]] if "estado" in f else "se anota"])
    frame = pd.DataFrame(rows, columns=w.COLUMNS).astype({c: float for c in w.NUMBERS})
    return blocks.table("Las tres composiciones", frame, w.TABLE_NOTE, digits=4) | {
        "compact": True, "help": w.HELP,
        "states": [[None] * (len(w.COLUMNS) - 1)
                   + [w.STATE[got["facts"]["estado"]] if "estado" in got["facts"] else None]
                   for got in measured.values()]}


def cloud(key: str, got: dict) -> dict:
    """One composition's cloud: every measured variant, the four quadrants, Spearman's line."""
    kept, f, cols = got["kept"], got["facts"], panel.columns(panel.KEYS[key])
    x, y = kept["e_is"].to_numpy(float), kept["e_oos"].to_numpy(float)
    group = np.where(kept["stratum"] == "origin", "Madre",
                     np.where(kept["top"], "Top de dentro", "Resto"))
    fit = None
    if "rho" in f and np.isfinite(f["rho"]):
        # The rank correlation drawn in the units of the cloud: through the two medians, with
        # the slope rho x IQR(out) / IQR(in). Least squares would hand the line to one point.
        spread = [np.subtract(*np.percentile(v, [75, 25])) for v in (x, y)]
        slope = f["rho"] * spread[1] / spread[0] if spread[0] > 0 else 0.0
        fit = {"slope": float(slope), "r": f["rho"],
               "intercept": float(np.median(y) - slope * np.median(x))}
    return {"kind": "scatter", "select": {"composición": name(key)},
            "title": f"Exceso por año: {cols['is_label']} (dentro) contra {cols['oos_label']} (fuera)",
            "x_label": f"exceso por año dentro — {cols['is_label']}",
            "y_label": f"exceso por año fuera — {cols['oos_label']}",
            "points": [{"x": float(a), "y": float(b), "label": str(v), "group": str(g)}
                       for a, b, v, g in zip(x, y, kept["variant_id"], group)],
            "quadrants": True, "fit": fit, "help": w.CLOUD_HELP,
            "note": w.CLOUD_NOTE + (
                f" Cuadrantes: {f['cuadrante_pp']} ganan dentro y fuera, {f['cuadrante_pn']} "
                f"sólo dentro, {f['cuadrante_np']} sólo fuera, {f['cuadrante_nn']} en ninguno."
                if "cuadrante_pp" in f else " Sin dato: la composición no se midió.")}


def annotated(measured: dict[str, dict], block_weeks: int) -> dict:
    """What is written beside the decision and never decides: one row per composition."""
    rows = [[key, *(got["facts"].get(k) for k in w.ANNOTATED)] for key, got in measured.items()]
    frame = pd.DataFrame(rows, columns=["Composición", *w.ANNOTATED.values()])
    frame[w.ANNOTATED["orden_bloque"]] = frame[w.ANNOTATED["orden_bloque"]].map(w.ORDER)
    numbers = [c for c in frame.columns[1:] if c != w.ANNOTATED["orden_bloque"]]
    frame = frame.astype({c: float for c in numbers})
    return blocks.table("Anotado sin decidir", frame,
                        w.ANNOTATED_NOTE.format(weeks=block_weeks), digits=4) | {
        "compact": True, "help": [None, *w.ANNOTATED_HELP]}


def filtered(measured: dict[str, dict]) -> dict:
    """How many variants each filter removed, per composition."""
    rows = [[label, *(got["facts"][k] for got in measured.values())]
            for k, label in w.FILTERS.items()]
    return blocks.table("Variantes por filtro", pd.DataFrame(
        rows, columns=["Filtro", *measured]), w.FILTERS_NOTE) | {"compact": True}


def tab(measured: dict[str, dict], deciding: str, block_weeks: int) -> dict:
    """The study's one tab.

    Args:
        measured: `c1`, `c2`, `c3` -> what `one.composition` returned.
        deciding: The key of the composition that decides; the cloud's selector opens on it.
        block_weeks: `annotate.block_weeks`, quoted under the annotated table.

    Returns:
        A tab: each composition's warnings, the table of the three, one cloud per
        composition under a selector, what is annotated, and the count per filter.
    """
    notes = [{"kind": "callout", "state": "watch", "text": f"{key}: {text}"}
             for key, got in measured.items() for text in got["notes"]]
    return envelope.tab(
        "orden", "¿Elegir por el pasado sirve fuera?",
        [*notes, compositions(measured), *(cloud(k, got) for k, got in measured.items()),
         annotated(measured, block_weeks), filtered(measured)],
        selectors=[{"key": "composición", "label": "Composición",
                    "options": [name(k) for k in measured], "default": name(deciding)}],
        note=w.TAB_NOTE)
