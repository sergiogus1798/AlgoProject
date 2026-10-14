# wfm/measure — the numbers

| file | what it does | in → out |
|---|---|---|
| `drift.py` | How far the optimiser's chosen tuple moves from one step to the next. | chosen → drift, stability |
| `equity.py` | Every cell's own out-of-sample equity on one comparable axis, and its statistics as a population. | trades → curves, rows |
| `excess.py` | Each trade's net excess with oos2 re-charged at its own costs, and the weekly oos2 panel. | trades, asset → per trade, weeks x cells, cell x segment |
| `gaterule.py` | SQX's own Walk-Forward Matrix pass/fail rule, over the conditions the export checked. | conditions, cells → score per cell; pass grid → best rectangle |
| `levels.py` | L1 and L2 on the weekly oos2 panel against the shared-sign flip null, and the cells' redundancy. | weeks x cells, signs → facts and null draws |

Must never hold: a threshold (they are `ledger:` rows read by `run.py`), a state word, or Spanish.

The null flips one sign per WEEK for all cells alike: it removes the edge and keeps what the cells
share. A count of cells would treat 2–4 effective curves as 30; the median does not.
