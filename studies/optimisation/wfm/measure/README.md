# walkForwardMatrix/measure — the numbers

| file | what it does | in → out |
|---|---|---|
| `correlation.py` | Does the chosen configuration's in-sample result predict the out-of-sample one? Per cell, then pooled over cells | steps → rho per cell, pooled interval |
| `drift.py` | How far the optimiser's tuple moves between steps, and which parameters it keeps re-deciding | chosen → drift, stability |

`per_cell` is the real measurement; `pooled` only summarises it. The interval comes from resampling
**cells**, never steps — see `../model/README.md` for the measurement that forces that.

`drift.per_step` normalises each parameter's move by its own spread across the export, so a period
moving by 3 and a shift moving by 3 are not treated as the same event.

Drift and correlation are one finding, not two. A surface with no out-of-sample signal has nothing
holding the optimiser in place, so it re-picks freely; high drift beside a near-zero correlation is
the coherent picture rather than a second, independent result.
