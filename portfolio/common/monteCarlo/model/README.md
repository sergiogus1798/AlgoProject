# monteCarlo/model — what are we pretending could have happened instead?

The assumptions, and the alternatives to them. Every module here answers "what would a different
draw of this history look like": another order, another composition, a worse fill, another calendar
slice, another volatility regime. They take a stream and produce *instructions* — an index matrix, a
P&L matrix, a set of positions, a bucket per trade — and never a conclusion.

This is the layer where the study can be wrong **without crashing**, so it is kept separate from the
execution that runs it: an assumption can be swapped and the same numbers recomputed under both,
which is the only way to find out whether a verdict depended on it.

**Imports from:** nothing inside the module — numpy and pandas only
**Consumed by:** `simulate/`, and `render/` for its label tables
**Must not contain:** a simulation loop, a percentile, a threshold, or any wording of a verdict

| file | what it does | run it | in → out |
|---|---|---|---|
| `stress.py` | **Family C.** Missed entries, worse costs, degraded fills toward each trade's own MAE, wider spread | imported | stream → P&L matrix |
| `windows.py` | The calendar slices: rolling windows, non-overlapping blocks, and the calendar split | imported | times → positions |

## Contracts and traps

- **Adding a way of randomising touches three things and nothing else.** Write a function in
  `engines/resample/draws.py` with the shared signature — `(n, size, rng, block)` in, an index matrix out — add it
  to `DRAWS`, say what it preserves in `PRESERVES`, and put it in `FAMILY`. A Family C perturbation
  is the same shape: a function in `stress.py` with `(stream, n, rng, cfg)`, a row in `MODELS` and
  in `TITLES`, and a floor in `verdict/gates.py`.
- **`KEEPS_MULTISET` is the honesty check.** The two models that only reorder — `iid_shuffle` and
  `block_shuffle` — must leave net profit identical to the last decimal. `sweeps.invariant()`
  measures it and every report prints it. **A non-zero there is a bug in the model, never a property
  of the strategy.**
- **The regime is daily whatever the trading timeframe is.** `atr_period` is in days, and `daily()`
  resamples the exported bars before anything else touches them.
- **Windows are defined in months, never in trades.** A window of "60 trades" moves with the
  strategy's own activity and stops being a calendar statement.
- **MAE arrives in account currency, not points**, and each trade has its own size —
  `fill_degrade` works off the already-converted per-trade distance, not off a price.

The reordering and resampling generators (`draws.py`) and the volatility regime (`regime.py`)
moved to `engines/resample/` and `engines/regimes/` on 2026-09-25: the cross-market portfolio and
the conditional map read them too, and a study must not import another.
