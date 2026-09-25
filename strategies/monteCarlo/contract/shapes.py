"""This study's histograms and percentile tables turned into contract blocks, in reading units."""

import numpy as np
import pandas as pd

from core.study import blocks
from strategies.monteCarlo.contract.words import LABELS, UNITS

# A share of the account is stored as a fraction and read as a percentage.
SCALE = {"%": 100.0}
TIER_STATE = {"STRONG": "pass", "ACCEPTABLE": "pass", "MARGINAL": "watch", "FAIL": "fail",
              "INCONCLUSIVE": "none"}


def scale(metric: str) -> float:
    """What a stored value of this statistic is multiplied by to be read in its unit."""
    return SCALE.get(UNITS[metric], 1.0)


def distribution(shape: dict, table: dict | None, metric: str, title: str,
                 note: str = "") -> dict:
    """One stored histogram as a "distribution" block.

    Args:
        shape: What metrics.shape() stored: counts over [lo, hi], observed, median, p_report.
        table: What metrics.summarise() stored for the same draws, or None where only the
            histogram was kept (a regime bucket, a window, an IS/OOS scope).
        metric: Key of words.LABELS, for the unit.
        title: What the reader is looking at.
        note: How to read it.

    Returns:
        The block. Without a table the band is unknown and only the report percentile is
        carried.
    """
    k = scale(metric)
    counts = shape["counts"]
    edges = np.linspace(shape["lo"], shape["hi"], len(counts) + 1) * k
    if table:
        pct = {str(q): v * k for q, v in table["p"].items()}
        band = [pct.get("5"), pct.get("95")]
        rank = table["rank"]
        note = note or (f"El backtest queda por encima del {rank:.0%} de las simulaciones."
                        if metric != "dd_pct" else
                        f"El backtest tuvo un drawdown mayor que el {rank:.0%} de las "
                        f"simulaciones.")
    else:
        pct, band = {}, [None, None]
    return {"kind": "distribution", "title": title, "unit": UNITS[metric],
            "bins": [float(e) for e in edges], "counts": [int(c) for c in counts],
            "real": shape["observed"] * k, "median": shape["median"] * k, "band": band,
            "percentiles": pct, "p": None, "note": note}


def summary(table: dict, metric: str, title: str) -> dict:
    """One sub-run's percentile table for one statistic, with its moments, as a table block."""
    k = scale(metric)
    rows = [[f"Percentil {q}", v * k] for q, v in table["p"].items()]
    rows += [["Media", table["mean"] * k], ["Mediana", table["median"] * k],
             ["Desviación estándar", table["std"] * k], ["Curtosis (exceso)", table["kurtosis"]],
             ["Backtest", table["observed"] * k], ["Simulaciones utilizables", table["n"]]]
    return blocks.table(title, pd.DataFrame(rows, columns=["qué", LABELS[metric]]))


def by_model(runs: dict, titles: dict, q: int, first: tuple[str, dict] | None = None) -> pd.DataFrame:
    """Every model of a family at one percentile, one column per statistic.

    Args:
        runs: {label: {metric: summarise()}}.
        titles: label -> readable name.
        q: The percentile read.
        first: An extra leading row, e.g. ("Backtest", observed statistics).

    Returns:
        A frame ready for blocks.table, shares already in percent.
    """
    rows = [[title] + [s[m]["p"][q] * scale(m) for m in LABELS]
            for title, s in ((titles[k], v) for k, v in runs.items())]
    if first:
        rows.insert(0, [first[0]] + [first[1][m] * scale(m) for m in LABELS])
    return pd.DataFrame(rows, columns=["modelo"] + [f"{v} ({UNITS[m]})" if UNITS[m] else v
                                                     for m, v in LABELS.items()])


def overlay(entry: dict, title: str) -> list[dict]:
    """The in-sample and out-of-sample halves of one degradation check, one block each."""
    return [distribution(entry[scope], None, entry["metric"], f"{title} — {scope}",
                         "Mismo modelo sobre sólo las operaciones de esta muestra.")
            for scope in ("IS", "OOS") if entry.get(scope) is not None]


def cone(band: dict, title: str, note: str) -> dict:
    """A fan.envelope() at 2.5/25/50/75/97.5 as a "cone" block, x in trade order."""
    return {"kind": "cone", "title": title, "unit": "USD", "x": band["at"],
            "bands": {str(q): v for q, v in band["bands"].items()},
            "real": band["observed"], "split": None, "note": note}
