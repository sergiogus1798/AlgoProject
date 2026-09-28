# screening/isOos — what the in-sample metrics say about the out-of-sample outcomes

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | The command: whichever halves this databank has input for, into one dated folder and one manifest naming both inputs | `python3 -m studies.screening.isOos.report --project XAUUSD --databank OOS [--set trades.bins=60]` | `metrics/<P>/<D>/metrics.csv` and/or the newest `harvest/<P>/<D>/<day>/` → `reports/<P>/<D>/<date>/isOos/` |
| `many.py` | The population half — the IS × OOS correlation map, persistence, one predictor ranking per outcome with the Benjamini-Hochberg survivors marked | imported | metrics columns → contract result |
| `one.py` | The per-trade half, one strategy: return, duration, MAE and MFE, IS and OOS overlaid as densities on shared bins, with the median shift and the two-sample KS p (encargo 24 E3, owner Q14) | imported | its harvest trades → contract result |
| `config.yaml` | The per-trade knobs: bins, and the tail share folded into the end bins | — | — |
| `tooltips.py` | One Spanish sentence per knob, for the window's drawer | imported | — |
| `panel.html` | Template for the interactive explorer. `__PAYLOAD__` is replaced with the embedded data | — | — |

## The per-trade half (encargo 24 E3)

Owner, 2026-09-27 (Q14): extend this study rather than open another; per-trade return, duration,
MAE and MFE yes; **the R multiple no** until the strategy carries a stop (step 24); never Net
Profit or drawdown, which grow with the window. Each is a `distribution` with two `series`
(IS, OOS) as densities of area 1 and a `shift` (`core/study/CONTRACT.md`); verdict None, no
`verdict.csv`. It reads only the samples `IS` and `OOS` and refuses a harvest carrying any other:
OOS2 is never read here. A strategy with no trade in one sample is skipped and counted in the
manifest.

- **The money columns come three ways** under the selector `unidad` — `USD` as exported, `% del
  saldo` (over the balance before the trade), `USD por lote` (over the size) — because the lot
  changes between samples (USDJPY 2026-09-27: median 3.3 IS, 4.6 OOS) and a USD shift would
  read sizing as edge. Which one the owner wants shown first is open; `USD` is first today only
  because it is the export's own number.
- **Bins** cover p0.5–p99.5 of both samples pooled; what falls outside is folded into the end
  bins, so each density keeps its area of 1 (`trades.tail_pct`).
- **Duration** is clock hours, weekends included. With an exit after X bars nearly every trade
  lasts the same, and the KS p on those ties is conservative.
- **Weight:** ~23 KB of JSON and ~23 KB of HTML per strategy — 200 strategies in 7 s and 9.4 MB;
  a 10,000-strategy harvest would write ~470 MB of pages.

The explorer is the last page that recomputes in a browser. It stays until the window has an IS/OOS
zone that filters; the contract result (`isOos.json`) is what the window reads today.

## The explorer: what the browser recomputes

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
