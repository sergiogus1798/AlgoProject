# screening/replication — do one databank's conclusions hold on another?

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | Per outcome: where each sample ended up against the reference, whether the reference's best filters delivered on each sample, and whether the samples rank the predictors alike | `python3 -m studies.screening.replication.report --project XAUUSD --reference OOS --databank OOS-sharpe` | several `metrics.csv` → `reports/<P>/<reference>/<date>/replication/` (owner, 2026-09-29: filed under the reference databank, not `_comparison`, so the window's Cribado tab can find it) |

Compare outcomes, never correlations: a sample selected on a metric has almost no variance left in
it, so its correlation collapses by construction. `../analysis/replication.py` has the argument.
