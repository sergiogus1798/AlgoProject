---
q: reconstruct SQX metrics from P/L vector, per-simulation metrics MC retest, WinLossRatio vs PayoutRatio, SQN formula, StandardDev ddof, DrawdownPct formula, RecoveryFactor, ZScore continuity, MaxLoss confidence level direction, non-reconstructible Sharpe Ulcer
tag: 🔬  date: 2026-09-18  see: sqx-format/mc-retest-storage, sqx-format/metric-formulas, columns/zero-pl-trades
---
# 29 of 97 varying metrics reconstruct exactly per simulation from the P/L vector
Capital-relative formulas with `MoneyManagement.InitialCapital` (100,000). Traps: `WinLossRatio` = count
ratio, `PayoutRatio` = avg win / avg loss; `AvgLoss` stored positive; `SQN = sqrt(min(n,100))·mean/sd`;
`StandardDev` is **ddof=0**; worse-when-higher metrics rank the other way (level 100 of `MaxLoss` is the
loss *closest to zero* — not a stress number). Sharpe, Sortino, Ulcer, RSquared, Stability use the
**daily curve** → no per-sim replication; never compare an analogue with SQX's stored value.

## Evidence
- Exact (rel. err < 2e-3) on `Strategy 1.19.29` original: NetProfit, GrossProfit/Loss, NumberOfTrades,
  NumberOfProfits/Losses, WinningPct, AvgWin, AvgTrade/Expectancy, StandardDev, Drawdown, ReturnDDRatio,
  MaxProfit/MaxLoss, MaxConsecWins/Losses, AvgConsecWins/Losses, KellyFormula.
- `WinLossRatio` 459/304 = 1.51; `PayoutRatio` 0.88; `KellyFormula` uses `PayoutRatio` as `R`. Signed
  `AvgLoss` is off by −2×. SQN 0.768 vs stored 0.77 (Van Tharp `sqrt(n)` gives 2.12 on 763 trades).
- `RSquared` is on the daily curve (0.9146 vs 0.92; trade-indexed 0.897). `Stability` (0.81) and
  `StabilitySQ3` (0.86) are separate, uncalibrated.
- Oracle: a formula is SQX's only if its order statistic reproduces the 11-level table — 11 × 5 = 55
  points per metric. On `MC Random IS 2.0` (worst rel. err):
  `DrawdownPct = max dd_k/(capital+peak_k)` [7e-4] (not dd/peak); `AvgDrawdown` = mean of `dd_k` over
  EVERY trade incl. zeros [4e-5] (in-drawdown only: 11 % off; episode maxima: 67 %);
  `AvgPctDrawdown` = mean `dd_k/(capital+peak_k)` incl. zeros [2e-3];
  `RecoveryFactor = NetProfit/(DrawdownPct·capital)` [5e-3] ≠ `ReturnDDRatio = NetProfit/Drawdown`;
  `ZScore = (R − mu_R + 0.5)/sigma_R` (error 0.046 → 0.014).
- Non-reconstructible: Sharpe-per-trade fails the table by 70 %, ×sqrt(12) by 56 %; trade-indexed Ulcer
  ≥ 61 %. Also `UlcerPerformanceIndex` (see metric-formulas).
- At scale: `MCR 1 Bar`..`MCR 8 Stress`, 5 strategies × 1,000 sims (39,996): **13,200 checks** (30 metrics
  × 11 levels × 5 × 8) reconcile, 16 failures (0.12 %), single levels in tasks 5 and 8, rank ties.
  `StandardDev` ddof=1 worst error 0.47, ddof=0 0.008; SQN can't tell (2 decimals). Sharpe-per-trade
  analogues must use ddof=0 too.
- Worse-when-higher (11): `GrossLoss`, `Drawdown`, `DrawdownPct`, `AvgDrawdown`, `AvgPctDrawdown`,
  `NumberOfLosses`, `AvgLoss`, `StandardDev`, `MaxConsecLosses`, `AvgConsecLosses`, `MaxLoss`; wrong
  direction gives rel. errors 0.88–0.94. `MaxLoss` level 100 on `MCR 5 Params / 23.16.37`: −1,743 while
  the worst sim had −8,494.
- ⚠️ `AvgAbsTrade` = constant 1.00215 × `mean(|p_i|)`, formula unknown, nearly invariant — exclude or
  mark approximate.
- The 29: NetProfit, GrossProfit/Loss, NumberOfTrades/Profits/Losses, WinningPct, AvgWin, AvgLoss,
  AvgTrade, Expectancy, AvgAbsTrade, StandardDev, Drawdown, DrawdownPct, AvgDrawdown, AvgPctDrawdown,
  ReturnDDRatio, RecoveryFactor, MaxProfit, MaxLoss, MaxConsecWins/Losses, AvgConsecWins/Losses,
  ProfitFactor, PayoutRatio, WinLossRatio, KellyFormula, SQN, ZScore. Rest exist only as 11 quantiles.
- Flat (zero-P/L) trades: `WinningPct` counts them half, `ZScore` as a win (columns/zero-pl-trades).
