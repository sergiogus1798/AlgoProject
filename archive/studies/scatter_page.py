#!/usr/bin/env python3
"""Build an interactive IS-vs-OOS scatter page from a metrics export.

Every in-sample metric gets a scatter panel against one out-of-sample metric,
and the OOS metric on the Y axis is switchable in the page. Panels re-sort by
correlation strength on each switch, so the best predictors lead.

Writes a single self-contained HTML file.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy import stats

TEMPLATE = Path(__file__).with_name("scatter_page.html")


def load(path):
    """Read the metrics export into named numeric columns.

    Inputs:
        path: Path to the ";"-separated CSV from export_metrics.py
    Output:
        (columns, names) where columns is dict {column name: list[float]} for
        every numeric column, and names is list[str] of strategy names.
    """
    rows = list(csv.DictReader(open(path), delimiter=";"))
    names = [r["Strategy Name"] for r in rows]
    columns = {}
    for key in rows[0]:
        try:
            columns[key] = [float(r[key]) for r in rows]
        except ValueError:
            pass
    return columns, names


def split_metrics(columns):
    """Separate the IS and OOS metric names, dropping constant columns.

    Inputs:
        columns: dict {column name: list[float]} from load
    Output:
        (is_metrics, oos_metrics), each list[str] of bare metric names with the
        " (IS)" / " (OOS)" suffix removed.

    A column SQX leaves at one value across every strategy has no correlation
    to compute, so it is excluded.
    """
    def pick(suffix):
        return [k[: -len(suffix)] for k, v in columns.items()
                if k.endswith(suffix) and np.std(v) > 0]
    return pick(" (IS)"), pick(" (OOS)")


def correlations(columns, is_metrics, oos_metrics):
    """Correlate every IS metric against every OOS metric, both ways.

    Inputs:
        columns: dict {column name: list[float]} from load
        is_metrics, oos_metrics: list[str] of bare metric names
    Output:
        dict {oos metric: {is metric: {"r", "p", "rs"}}} where r and p are
        Pearson and its two-tailed p-value, and rs is Spearman.

    Pearson is the headline because a linear acceptance threshold implies a
    linear relationship. Spearman rides along because these metrics are
    heavy-tailed and the two disagreeing is a warning about outliers.
    """
    out = {}
    for target in oos_metrics:
        y = columns[f"{target} (OOS)"]
        out[target] = {}
        for m in is_metrics:
            x = columns[f"{m} (IS)"]
            pearson = stats.pearsonr(x, y)
            out[target][m] = {"r": round(float(pearson.statistic), 4),
                              "p": round(float(pearson.pvalue), 5),
                              "rs": round(float(stats.spearmanr(x, y).statistic), 4)}
    return out


def critical_r(n, alpha=0.05):
    """Smallest |r| that is significant at the given level.

    Inputs:
        n: int, sample size
        alpha: float, two-tailed significance level
    Output:
        float, the critical correlation.
    """
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    return float(t / np.sqrt(n - 2 + t ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    columns, names = load(a.metrics)
    is_metrics, oos_metrics = split_metrics(columns)
    is_metrics.sort()
    oos_metrics.sort()

    payload = {
        "n": len(names),
        "rcrit": round(critical_r(len(names)), 3),
        "strategies": names,
        "is": is_metrics,
        "oos": oos_metrics,
        "data": {k: columns[k] for k in columns},
        "stats": correlations(columns, is_metrics, oos_metrics),
        "source": a.metrics.name,
    }
    html = TEMPLATE.read_text().replace("__PAYLOAD__", json.dumps(payload))
    a.out.write_text(html)
    print(f"wrote {a.out}: {len(is_metrics)} IS metrics x "
          f"{len(oos_metrics)} OOS targets, n={len(names)}")


if __name__ == "__main__":
    main()
