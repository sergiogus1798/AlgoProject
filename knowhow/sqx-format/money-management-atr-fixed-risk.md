---
q: which money management do the strategies use, ATRRiskBasedSizingFixedRisk parameters, why does Size vary per trade, risk per trade in SQX, convert SQX P&L to another risk or stop, lastSettings.xml MoneyManagement use=true, fixed risk R multiple
tag: 🔬  date: 2026-09-30  see: export/orderstocsv-schema, sqx-format/daily-equity-bin
---
# The workflow's strategies size every trade at a FIXED $1,000 risk over 4·ATR(20) — SQX's P&L is already fixed-risk
The active method in `lastSettings.xml` (`Method[@use="true"]`) is `ATRRiskBasedSizingFixedRisk`:
`Amount` 1000 (USD per trade, on the 100k initial — not compounding), `ATRPeriod` 20, `ATRMult` 4,
`Decimals` 2, `LotsIfNoMM` 0.01, `MaxLots` 500. So `Size` varies trade by trade with the ATR. At risk
r of an account S with a stop of X·ATR(20), a trade's P&L = SQX's × **4 / (1000 · X)** × r · S — one
constant per strategy (`portfolio/common/construct/inputs/risk.py`). A stop grafted by step 24 is a
different number (`StopLossCoef1`), read from the strategy itself.

## Evidence
- Archived USDJPY M30 `4d679e…/2026-09-28T0919/strategy.sqx`, 2026-09-30: every other method in
  `lastSettings.xml` has `use="false"`; `settings.xml` `MoneyManagement.UseFromStrategy` false,
  `InitialCapital` 100000; its 2,094 trades' `Size` runs 0.68-15.37 (median 3.67).
- `tests/test_portfolio_search.py`: the mapping read back, and X read from a stop grafted in memory.
