# walkForwardMatrix/model — what this geometry lets you claim

| file | what it does | in → out |
|---|---|---|
| `windows.py` | Window lengths and overlap per cell, the unit of observation that follows from them, and whether the chosen metric is contaminated by window length | steps → shapes, rules, warning |

## The measurement that decides every inference below it

🔬 Measured 2026-09-10 on `XAUUSD/WFM`, cell 6 runs / 20 % OOS:

- The **run windows are disjoint and consecutive** — 0 overlaps across all 60 cells. A cell's steps
  are therefore separate draws in time, and a correlation over them is honest at n = steps.
- The **optimisation windows overlap by 6.5 of 8.2 years, 79 %**. The in-sample side of every pair
  is heavily autocorrelated. That does not bias the correlation; it is why cell-level figures move
  together and why their spread is not a standard error.
- **Every cell re-splits the same history.** 30 cells are 30 views of one dataset. Pooling their 330
  steps into one correlation would give an interval several times narrower than the data supports.

So: **the cell is the unit.** `measure/correlation.py` bootstraps over cells, and even that is a
floor on the uncertainty rather than a measure of it, because cells are not exchangeable either.

## The length trap the matrix builds in on purpose

The `runs` axis changes how long each window is — more runs means shorter windows. Ret/DD, Calmar,
NetProfit and CAGR all grow with the horizon (return goes as mu*T, maximum drawdown as
sigma*sqrt(T)), so a trend along that axis on one of them is partly the axis itself.
`length_warning()` emits the sentence when the ratio of longest to shortest window exceeds 5 %, and
the report carries it above the axis tables rather than leaving the reader to remember.
