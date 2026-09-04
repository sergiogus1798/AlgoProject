# 2_tasks/reports — rendering a population study

| file | what it does | run it | in → out |
|---|---|---|---|
| `is_oos.py` | The IS/OOS study: reads a databank's current metrics export, writes one dated report | `python3 2_tasks/reports/is_oos.py --project XAUUSD --databank OOS` | `metrics/<P>/<D>/metrics.csv` → `reports/<P>/<D>/<date>/explorer.html` + `summary.md` |
| `summary.py` | Turns computed correlation rows into `summary.md`. Pure text, computes nothing | imported | rows → markdown |
| `panel.html` | Template for the interactive panel. `__PAYLOAD__` is replaced with the embedded data | — | — |

## The split between Python and the browser

**Python states the conclusions over the whole population** and writes them into `summary.md`:
persistence, predictor rankings, and which of them survive Benjamini-Hochberg. Each report directory
also gets its own `manifest.json` — which metrics export it read, the export's own date, and the
commit that produced both — so a report and the CSV it was built from can drift and still be told
apart (`core/manifest.py`).

**The panel recomputes in the browser**, because a filter changes `n` and therefore changes every
statistic. It carries every strategy for that reason, which is why `explorer.html` is a few
megabytes. Its Spearman and Pearson agree with SciPy to three decimals; its p-value uses a Fisher
z-transform rather than the exact t-distribution, which is accurate from about n=20 up.

## What the panel does

- **Y axis** switches the out-of-sample outcome. Panels re-sort by |ρ| on every change, strongest first.
- **Points drawn per panel** limits only the dots painted, default 100. Every statistic, the
  regression and the histogram use every strategy that passes the filter. The sample is seeded and
  is the same set of strategies in every panel, so one strategy can be followed across them.
- **Histogram** along the bottom of each panel is the share of the population per bin of the X
  metric. It is there to answer "is the regression being carried by a handful of points in one
  tail?", which the correlation alone cannot say.
- **Axis range** defaults to p1–p99 of the full population. It stays fixed under filtering, so the
  subset visibly occupies its corner. Points outside are not drawn but are still in the statistics.
- **Filter** clauses are each evaluated against the **full** population, then ANDed — "top 20%" means
  the top 20% of all 10,000, not of whatever a previous clause left. Under a filter the whole
  population stays behind in grey and every statistic is recomputed on the survivors.

The header line is the first hint of what `../TODO.md` is for: it reports the median outcome of the
survivors against the median of everything.
