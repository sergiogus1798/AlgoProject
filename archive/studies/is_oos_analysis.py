#!/usr/bin/env python3
"""Which in-sample metrics predict out-of-sample performance?

Reads the CSV export_metrics.py wrote and correlates every IS metric against
the OOS outcomes, so strategy selection can be based on what actually carries
forward rather than on what looks good in-sample.

Writes summary.txt, correlations.csv and three figures into --out.
"""

import argparse
import csv
from pathlib import Path

import numpy as np
from scipy import stats

import plots_is_oos

# Metrics present as both "<name> (IS)" and "<name> (OOS)" in the export.
PAIRED = ["Net profit", "# of trades", "Profit factor", "Sharpe Ratio", "PSR",
          "SQN", "R Expectancy", "Annual % Return", "CAGR", "Drawdown",
          "Max DD %", "Open Drawdown", "Ret/DD Ratio", "CAGR/Max DD %",
          "Stability", "Stagnation", "RSquared", "Symmetry", "Winning Percent",
          "Win/Loss ratio", "Payout ratio", "Avg. Trade", "Avg. Abs Trade",
          "Avg. Win", "Avg. Loss", "Avg. Bars Win", "Avg. Bars Loss",
          "Avg. Bars in Trade", "Exposure", "Commission/Swap ($)"]

# What we are trying to predict.
TARGETS = ["Profit factor", "Sharpe Ratio", "Ret/DD Ratio", "Net profit"]

# Scattered IS against OOS. These are the metrics a selection rule would use;
# the most *persistent* metrics are structural (bars held, trade count) and
# carry no information about edge, so ranking by persistence picks the wrong six.
FOCUS = ["Profit factor", "Sharpe Ratio", "Ret/DD Ratio", "Winning Percent",
         "Stability", "Net profit"]


def load(path):
    """Read the metrics export into named numeric columns.

    Inputs:
        path: Path to the ";"-separated CSV from export_metrics.py
    Output:
        (columns, names) where columns is dict {column name: np.ndarray of
        float} and names is list[str] of strategy names.
    """
    rows = list(csv.DictReader(open(path), delimiter=";"))
    names = [r["Strategy Name"] for r in rows]
    columns = {}
    for key in rows[0]:
        try:
            columns[key] = np.array([float(r[key]) for r in rows])
        except ValueError:
            pass
    return columns, names


def correlate(x, y):
    """Pearson and Spearman correlation between two metric columns.

    Inputs:
        x, y: np.ndarray of float, same length
    Output:
        dict with keys pearson, spearman, p (float; p is the Spearman
        two-tailed p-value).

    Spearman is the one to trust here: these metrics have heavy tails and a
    single blow-up strategy dominates Pearson.
    """
    pearson = stats.pearsonr(x, y)
    spearman = stats.spearmanr(x, y)
    return {"pearson": pearson.statistic,
            "spearman": spearman.statistic,
            "p": spearman.pvalue}


def critical_r(n, alpha=0.05):
    """Smallest |Spearman r| that is significant at the given level.

    Inputs:
        n: int, sample size
        alpha: float, two-tailed significance level
    Output:
        float, the critical correlation.
    """
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    return t / np.sqrt(n - 2 + t ** 2)


def varying(columns):
    """The paired metrics that actually vary in this export.

    Inputs:
        columns: dict {column name: np.ndarray} from load
    Output:
        list of str, metric names whose IS and OOS columns are both non-constant.

    A metric SQX leaves at a fixed value (PSR and Symmetry are 1.0 and 0.0 here)
    has no correlation to compute, so it is excluded rather than reported as NaN.
    """
    return [m for m in PAIRED
            if columns[f"{m} (IS)"].std() > 0 and columns[f"{m} (OOS)"].std() > 0]


def persistence(columns):
    """How well each metric holds its own value from IS to OOS.

    Inputs:
        columns: dict {column name: np.ndarray} from load
    Output:
        list of dict sorted by descending spearman, each with keys metric,
        is_mean, oos_mean, decay (OOS/IS as a ratio), pearson, spearman, p.
    """
    out = []
    for m in varying(columns):
        x, y = columns[f"{m} (IS)"], columns[f"{m} (OOS)"]
        row = {"metric": m, "is_mean": x.mean(), "oos_mean": y.mean(),
               "decay": y.mean() / x.mean() if x.mean() else np.nan}
        row.update(correlate(x, y))
        out.append(row)
    return sorted(out, key=lambda r: -abs(r["spearman"]))


def predictors(columns, target):
    """Rank every IS metric by how well it predicts one OOS outcome.

    Inputs:
        columns: dict {column name: np.ndarray} from load
        target: str, the OOS metric to predict, e.g. "Profit factor"
    Output:
        list of dict sorted by descending |spearman|, each with keys metric,
        pearson, spearman, p.
    """
    y = columns[f"{target} (OOS)"]
    out = []
    for m in varying(columns):
        row = {"metric": m}
        row.update(correlate(columns[f"{m} (IS)"], y))
        out.append(row)
    return sorted(out, key=lambda r: -abs(r["spearman"]))


def table(rows, columns):
    """Render rows as a fixed-width text table.

    Inputs:
        rows: list of dict
        columns: list of (key, header, format spec)
    Output:
        str, the table including its header rule.
    """
    cells = [[r[k] if f == "" else format(r[k], f) for k, _, f in columns]
             for r in rows]
    widths = [max([len(h)] + [c[i] and len(c[i]) for c in cells])
              for i, (_, h, _) in enumerate(columns)]
    head = "  ".join(h.rjust(w) for (_, h, _), w in zip(columns, widths))
    lines = [head, "-" * len(head)]
    for row in cells:
        lines.append("  ".join(c.rjust(w) for c, w in zip(row, widths)))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    columns, names = load(a.metrics)
    n = len(names)
    r_crit = critical_r(n)

    persist = persistence(columns)
    ranked = {t: predictors(columns, t) for t in TARGETS}

    lines = [
        f"{n} strategies from {a.metrics.name}",
        f"Significance floor at n={n}: |r| > {r_crit:.3f} (Spearman, p<0.05).",
        "Anything below that is noise no matter how it reads.",
        "",
        "=" * 78,
        "PERSISTENCE - does a metric keep its value out of sample?",
        "=" * 78,
        "",
        table(persist, [("metric", "metric", ""), ("is_mean", "IS mean", ",.2f"),
                        ("oos_mean", "OOS mean", ",.2f"),
                        ("decay", "OOS/IS", ".2f"),
                        ("spearman", "spearman", "+.3f"), ("p", "p", ".4f")]),
    ]

    for target in TARGETS:
        keep = [r for r in ranked[target] if r["metric"] != target][:12]
        lines += [
            "",
            "=" * 78,
            f"PREDICTING OOS {target.upper()} from in-sample metrics",
            "=" * 78,
            "",
            table(keep, [("metric", "IS metric", ""),
                         ("spearman", "spearman", "+.3f"),
                         ("pearson", "pearson", "+.3f"), ("p", "p", ".4f")]),
        ]

    strong = [r for r in ranked["Profit factor"]
              if abs(r["spearman"]) > r_crit and r["metric"] != "Profit factor"]
    lines += [
        "",
        "=" * 78,
        "FINDINGS",
        "=" * 78,
        "",
        f"  Metrics that survive the significance floor for OOS profit factor: "
        f"{len(strong)} of {len(varying(columns))}.",
    ]
    for r in strong:
        direction = "higher is better" if r["spearman"] > 0 else "LOWER is better"
        lines.append(f"    {r['metric']:<24} r={r['spearman']:+.3f} "
                     f"p={r['p']:.4f}   ({direction})")
    if not strong:
        lines.append("    none - no in-sample metric predicts OOS profit factor "
                     "at this sample size.")

    report = "\n".join(lines)
    print(report)
    (a.out / "summary.txt").write_text(report)

    with open(a.out / "correlations.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["target", "is_metric", "spearman", "pearson", "p"])
        for target in TARGETS:
            for r in ranked[target]:
                w.writerow([target, r["metric"], f"{r['spearman']:.4f}",
                            f"{r['pearson']:.4f}", f"{r['p']:.5f}"])

    plots_is_oos.plot_persistence(persist, r_crit, a.out / "fig1_persistence.png")
    by_metric = {r["metric"]: r for r in persist}
    plots_is_oos.plot_scatter_grid(columns, [by_metric[m] for m in FOCUS],
                                   a.out / "fig2_scatter.png")
    plots_is_oos.plot_predictors(ranked["Profit factor"], r_crit,
                                 "OOS profit factor",
                                 a.out / "fig3_predictors.png")


if __name__ == "__main__":
    main()
