# wfm/measure — the numbers

| file | what it does | in → out |
|---|---|---|
| `excess.py` | Each trade's net excess — SQX's P/L, minus the oos2 re-charge where it closes in oos2, minus the market's drift — the weekly oos2 panel (unit = cell, whole trade in its closing week) and each unit's excess per year by segment | trades, asset → per trade, weeks x cells, cell x segment |
| `levels.py` | L1 (median cell's excess per year against the shared-sign null), the reference series, L2 (reference − mother, same sign sets), effective cells from the correlation matrix's eigenvalues, and the weekly median's skewness | weeks x cells, signs → facts and null draws |
| `gaterule.py` | SQX's per-cell pass/fail rule and its area check; `oos_only` first rescales every `score` value to the out-of-sample alone (x `oos_`/`all_` metric) and re-decides `met` | conditions, cells → score per cell; pass grid → best rectangle |
| `drift.py` | How far the optimiser's tuple moves between steps over the mother's OWN parameters, and which it keeps re-deciding | chosen → drift, stability |
| `equity.py` | Every cell's out-of-sample equity on percent-of-trades-done, each cell's figures and their spread, and each cell against the original over the same windows | trades → curves, rows |

Must never hold: a threshold (they are `ledger:` rows read by `run.py`), a state word, or Spanish.

The null flips one sign per WEEK for all cells alike: it removes the edge and keeps what the cells
share. A count of cells would treat 2–4 effective curves as 30; the median does not.
