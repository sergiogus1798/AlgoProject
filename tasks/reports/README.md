# tasks/reports — rendering a population study

| file | what it does | run it | in → out |
|---|---|---|---|
| `is_oos.py` | The IS/OOS study: reads a databank's current metrics export, writes one dated report | `python3 -m tasks.reports.is_oos --project XAUUSD --databank OOS` | `metrics/<P>/<D>/metrics.csv` → `reports/<P>/<D>/<date>/explorer.html` + `summary.md` |
| `filters.py` | The filter sweep: what each candidate IS filter buys on an OOS outcome, corrected across the sweep | `python3 -m tasks.reports.filters --project XAUUSD --databank OOS` | `metrics/<P>/<D>/metrics.csv` → `reports/<P>/<D>/<date>/filters/improvement.md` |
| `compare.py` | The replication check: do one databank's conclusions hold on other, independently generated databanks | `python3 -m tasks.reports.compare --project XAUUSD --reference OOS --databank OOS-sharpe` | several `metrics.csv` → `reports/<P>/_comparison/<date>/comparison.md` |
| `decay.py` | The decay verdict: per strategy, how much edge survived out of sample and whether to keep it | `python3 -m tasks.reports.decay --project XAUUSD --databank OOS --split 2018-01-01 --end 2022-12-31` | the databank's `.sqx` → `reports/<P>/<D>/<date>/decay.csv` + `decay.md` |
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

- **Correlation map** crosses every IS metric against every OOS metric on the population the filter
  leaves. Its colour scale is discrete — twenty steps — and its extent is the 95th percentile of the
  values shown rather than −1…+1, because these correlations live inside ±0.3 and a full-range scale
  paints every cell the same. A cell carrying a dot survives Benjamini-Hochberg within its own
  column; clicking one moves that OOS metric to the Y axis.
- **Strategy table** lists the survivors with every metric, sortable by any column.
- **The closing section** explains r, ρ, the p-value and Benjamini-Hochberg, since the panel is read
  by whoever the owner shows it to and the three numbers are not self-explanatory.

The header line is what `filters.py` generalises: it reports the median outcome of the survivors
against the median of everything, for one filter the owner typed. The sweep does it over 210
candidates at once, with the interval and the correction that a single typed filter cannot have.
It writes into `<date>/filters/` rather than the report directory itself, so its manifest and the
IS/OOS study's manifest do not overwrite each other.
