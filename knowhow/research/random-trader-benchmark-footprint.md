---
q: Why was benchmark=0 the wrong null for PSR, and what does footprint() price instead?
kw: PSR benchmark 0 wrong null OPEN.md #71, crossmarket monteCarlo mcRetest benchmark, footprint noise bug total variance, p_positive 1.0 to 0.0, same-footprint random trader
tag: 🔬  date: 2026-09-29  see: research/random-entry-nulls, research/random-trader-oos-only, research/mintrl-explosion-is-correct
---
# `benchmark=0` was the wrong null: price a same-footprint random trader against the market's own noise
`benchmark=0` was the wrong null; `footprint()` now prices a same-footprint random trader against the market's own bar-to-bar noise (law of total variance), shared by `crossmarket`, `monteCarlo` and `mcRetest` — see Evidence.

## Evidence
**Footprint fix, 🔬 2026-09-29.** mcRetest, `Test_USDJPY_donchianUpperCrossUp_M30` (real ingest, read-only, session algoproject-36's data): before, benchmark +2.0 to +2.2/strategy, `p_positive` 1.0→0.0 for all five checked; after, benchmark +0.004 to +0.006, `p_positive` back to 1.0. `analytic_sharpe`'s own `psr` stays ≈1.0 either side — a separate scale mismatch (summed, not per-trade, `returns`), still open.
crossmarket, real USDJPY M30 bars 2018–2022 through the study's own `backtest.setting()`/`exposure.run()` (no XAUUSD trade harvest on disk to run the real pipeline on): before, benchmark **-11.18** (mu_m≈+2e-6/bar, near-zero drift, so a near-constant series driven to an extreme Sharpe by holding-time alone), `psr=1.000000`; after (sigma_m≈7.1e-4/bar), benchmark **-0.070**, `psr=0.556` against an observed Sharpe of -0.062 — plausible instead of saturated.

