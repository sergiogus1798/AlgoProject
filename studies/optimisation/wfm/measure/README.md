# walkForwardMatrix/measure — the numbers

| file | what it does | in → out |
|---|---|---|
| `correlation.py` | Does the chosen configuration's in-sample result predict the out-of-sample one? Per cell, then pooled over cells | steps → rho per cell, pooled interval |
| `drift.py` | How far the optimiser's tuple moves between steps, and which parameters it keeps re-deciding | chosen → drift, stability |
| `gaterule.py` | SQX's own per-cell pass/fail rule and its area check — tie-break and recommended centre included — over every condition `export_wfm` checked per cell; `legacy` scores an export older than 2026-10-01 on its 2 `oos` conditions (encargo 37) | conditions.parquet → score per cell; pass grid → best rectangle, centre |
| `equity.py` | Every cell's out-of-sample equity, resampled onto percent-of-trades-done so cells overlay; each cell's net profit, PF, daily Sharpe and DD, and their spread across cells | trades.parquet → one curve per cell, one row per cell, aggregate table |

`per_cell` is the real measurement; `pooled` only summarises it. The interval comes from resampling
**cells**, never steps — see `../model/README.md` for the measurement that forces that.

`drift.per_step` normalises each parameter's move by its own spread across the export, so a period
moving by 3 and a shift moving by 3 are not treated as the same event.

Drift and correlation are one finding, not two. A surface with no out-of-sample signal has nothing
holding the optimiser in place, so it re-picks freely; high drift beside a near-zero correlation is
the coherent picture rather than a second, independent result.
