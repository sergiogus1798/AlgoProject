"""What every cross-market tab builds from: a stored histogram, a cone, a metric table, plain text."""

import re

import numpy as np
import pandas as pd

from core.study import blocks
from studies.transfer.crossmarket.simulate import metrics

TAGS = re.compile(r"<[^>]+>")
UNIT = {"$": "USD", "%": "%", "": ""}


def text(html: str) -> str:
    """A sentence written for the old HTML panel, with its markup removed for the window."""
    return re.sub(r"\s+", " ", TAGS.sub("", html)).strip()


def distribution(shape: dict, metric: str, title: str, note: str = "",
                 p: float | None = None) -> dict:
    """One stored histogram (metrics.shape) as a "distribution" block.

    Args:
        shape: counts over [lo, hi], observed, median, lo_ci and hi_ci (2.5 and 97.5).
        metric: Key of metrics.LABELS, for the unit.
        title: What the reader is looking at.
        note: How to read it; by default, how many simulations the real run beat.
        p: The empirical p, when the metric table carries it.

    Returns:
        The block; its band is the 2.5–97.5 the study reports.
    """
    counts = shape["counts"]
    worse = "sufrieron más" if not shape["higher_is_better"] else "rindieron peor"
    return {"kind": "distribution", "title": title, "unit": UNIT.get(metrics.UNITS[metric], ""),
            "bins": list(np.linspace(shape["lo"], shape["hi"], len(counts) + 1)),
            "counts": counts, "real": shape["observed"], "median": shape["median"],
            "band": [shape["lo_ci"], shape["hi_ci"]],
            "percentiles": {"2.5": shape["lo_ci"], "50": shape["median"],
                            "97.5": shape["hi_ci"]}, "p": p,
            "note": note or f"El {shape['beats']:.1%} de las simulaciones {worse} que el "
                            f"backtest real en {metrics.LABELS[metric]}."}


def cone(run_cone: dict, title: str, note: str = "") -> dict:
    """A run's equity cone — bands on the calendar, the real curve over them — as a block."""
    return {"kind": "cone", "title": title, "unit": "USD", "x": run_cone["dates"],
            "bands": {f"{q:g}": v for q, v in run_cone["bands"].items()},
            "real": run_cone["observed"], "split": None, "note": note}


def metric_table(table: dict, cfg: dict, title: str) -> dict:
    """Every statistic of one simulated run against the real backtest, percentiles included."""
    qs = cfg["equity"]["percentiles"]
    rows = [[metrics.LABELS[n] + (" (más es mejor)" if metrics.HIGHER_IS_BETTER[n]
                                  else " (menos es mejor)"),
             v["observed"], v["median"], v["p_value"], v["beats"], *[v["p"][q] for q in qs]]
            for n, v in ((n, table[n]) for n in metrics.TABLED if n in table)]
    alpha = cfg["diagnostics"]["alpha"]
    return blocks.table(title, pd.DataFrame(
        rows, columns=["estadístico", "real", "mediana simulada", "p", "bate a",
                       *[f"p{q:g}" for q in qs]]),
        f"p: qué fracción de las simulaciones igualó o superó al real en ese indicador; "
        f"cuanto más pequeño, más difícil de explicar por suerte (criterio {alpha:.2f}). "
        f"«Bate a» es la otra cara. En drawdown y racha perdedora ambos se calculan con "
        f"«menos es mejor».")


def on_axis(curves: dict[str, dict], key: str) -> tuple[list[str], dict[str, list]]:
    """Several dated curves on one shared calendar axis.

    Args:
        curves: {name: {"dates": [...], key: [...]}}, each on its own dates.
        key: Which series of each curve to place.

    Returns:
        (dates, {name: values}). A curve holds its last value until its next point — equity
        moves in steps, on exits — and is None before its first date, so a market whose
        backtest starts later starts later on the chart instead of breaking into dots.
    """
    dates = sorted({d for c in curves.values() for d in c["dates"]})
    out = {}
    for name, c in curves.items():
        at, last, values = dict(zip(c["dates"], c[key])), None, []
        for d in dates:
            last = at.get(d, last)
            values.append(last if d <= c["dates"][-1] else None)
        out[name] = values
    return dates, out


def bars(title: str, items: list[tuple[str, float]], unit: str, reference: float | None,
         note: str = "", good: float | None = None) -> dict:
    """One bar per market; green above `good` (or the reference) and red below it."""
    cut = good if good is not None else reference
    return {"kind": "bars", "title": title, "unit": unit, "reference": reference, "note": note,
            "items": [{"label": k, "value": v, "error": None,
                       "state": "info" if cut is None or v != v else
                       "pass" if v > cut else "fail"} for k, v in items]}
