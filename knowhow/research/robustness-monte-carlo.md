---
q: Monte Carlo drawdown inflation, backtest drawdown underestimates real, stitched 5th percentile path, how many simulations, 20000 vs 100000, reorder invariant net profit, prop firm drawdown veto, edge dies after 2013
tag: 🔬  date: 2026-09-09  see: perf/monte-carlo-bandwidth
---
# Size the account on ~2× the backtest drawdown; 20,000 sims already decide
Median drawdown inflation (95th pct reordered DD / observed) is 1.95 — backtest DD is about half the real one.
Compare prop-firm rules against the stitched worst-block path (~4–5× observed), read as an order of magnitude.
20,000 simulations fix every verdict; 100,000 only sharpens tails. No seed anywhere, on purpose. Reordering
without replacement must leave net profit identical (`sweeps.invariant()` ≈ 1e-11 $); if not, the model touches composition.

## Evidence
36 strategies of `XAUUSD/Results` (export `raw/XAUUSD/Results/2026-09-03/trades/`, report
`AlgoData/reports/XAUUSD/Results/2026-09-09/montecarlo/`):
`python3 -m strategies.monteCarlo.report --project XAUUSD --databank Results --asset XAUUSD --export 2026-09-03`
- DD inflation median 1.95, min 1.52; pure order effect, no trade changes.
- `Strategy 18.28.28`: 2.4 % observed → 4.4 % at p95 reordering → 9–12 % stitched (5th pct of every two-year block). Stitched path moves more between runs.
- Edge dies after 2013: 24-month rolling windows positive early, negative later for almost all; 29–30 of 36 have a
  non-overlapping 24-month block with negative resampled median (±1–2 between runs, blocks near zero). No databank column shows it.
- Median OOS Sharpe ≈ 0.13–0.14 × IS (level comparison, not an overfitting test).
- Stability: 8 repeats with fresh entropy, most-moving percentile (DD 99th) varies 2–4 % of mean at 20,000; 1.2–1.3 % at 100,000; all 36 verdicts same.
  36 strategies × 100,000, six block sizes + stability: 15 min on 96 cores.
- 🤔 The 10 %-of-account DD ceiling vetoes 21 of 36 at $1,000 risk/trade on $100,000 — a statement about position size as much as strategy; provisional until prop-firm rules are known.
